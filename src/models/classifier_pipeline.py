import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score, 
    roc_auc_score,
    ConfusionMatrixDisplay
)

class ClassifierPipeline:
    def __init__(self, db_manager, test_size=0.2, max_features=5000):
        self.db_manager = db_manager
        self.test_size = test_size
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=max_features)
        
        self.nb_model = MultinomialNB()
        self.svm_model = SVC(kernel='linear', probability=True) # probability=True is needed to calculate AUC-ROC

    def run_training_pipeline(self, output_dir="results"):
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Fetch ML Dataset (excluding neutral class as done in JATI paper)
        print("Loading data from SQLite database...")
        df = self.db_manager.get_ml_dataset(exclude_neutral=True)
        
        if len(df) < 10:
            print(f"Dataset is too small ({len(df)} samples). Please scrape and label more data first.")
            return None
            
        print(f"Dataset distribution: {df['label'].value_counts().to_dict()}")
        
        X = df['cleaned_text'].values
        y = df['label'].values
        
        # Convert label strings to binary 0/1 for metric calculations (e.g. negative=0, positive=1)
        y_binary = np.where(y == 'positive', 1, 0)
        
        # 2. Stratified train/test split (80:20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_binary, 
            test_size=self.test_size, 
            stratify=y_binary, 
            random_state=42
        )
        
        print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
        
        # 3. TF-IDF unigram-bigram extraction
        print("Extracting TF-IDF features...")
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # 4. Train & Evaluate Naive Bayes
        print("Training Multinomial Naive Bayes...")
        self.nb_model.fit(X_train_vec, y_train)
        nb_preds = self.nb_model.predict(X_test_vec)
        # Handle cases where Naive Bayes only predicts one class due to severe imbalance
        nb_probs = self.nb_model.predict_proba(X_test_vec)[:, 1] if len(np.unique(y_train)) > 1 else np.zeros_like(y_test)
        
        # 5. Train & Evaluate SVM
        print("Training Support Vector Machine (Linear Kernel)...")
        self.svm_model.fit(X_train_vec, y_train)
        svm_preds = self.svm_model.predict(X_test_vec)
        svm_probs = self.svm_model.predict_proba(X_test_vec)[:, 1] if len(np.unique(y_train)) > 1 else np.zeros_like(y_test)
        
        # 6. Compute Metrics
        results = {
            "Naive Bayes": self.compute_metrics(y_test, nb_preds, nb_probs),
            "SVM": self.compute_metrics(y_test, svm_preds, svm_probs)
        }
        
        # 7. Generate Classification Report and Confusion Matrices
        self.save_confusion_matrix(y_test, nb_preds, "Naive Bayes", os.path.join(output_dir, "nb_confusion_matrix.png"))
        self.save_confusion_matrix(y_test, svm_preds, "SVM (Linear)", os.path.join(output_dir, "svm_confusion_matrix.png"))

        # Keep raw confusion matrices for the textual report (tujuan 2 & 3)
        cm_data = {
            "Naive Bayes": confusion_matrix(y_test, nb_preds),
            "SVM": confusion_matrix(y_test, svm_preds)
        }
        
        # 8. Print comparison table
        results_df = pd.DataFrame(results).T
        print("\n=== CLASSIFIER COMPARISON REPORT ===")
        print(results_df.to_markdown())
        print("====================================")
        print(f"Confusion matrix plots saved in '{output_dir}/'")
        
        # Export results to CSV
        results_df.to_csv(os.path.join(output_dir, "comparison_results.csv"))
        
        # Plot comparison bar chart
        self.plot_comparison(results_df, os.path.join(output_dir, "comparison_plot.png"))
        
        # 9. Predict sentiment over the full dataset to conclude public opinion on MBG
        df_all = self.db_manager.get_ml_dataset(exclude_neutral=False)
        X_all_vec = self.vectorizer.transform(df_all['cleaned_text'].values)
        sentiment_dist = {}
        for model_name, model in [("Naive Bayes", self.nb_model), ("SVM", self.svm_model)]:
            all_preds = model.predict(X_all_vec)
            sentiment_dist[model_name] = {
                "positive": int((all_preds == 1).sum()),
                "negative": int((all_preds == 0).sum())
            }
        # Generate and save textual summary report
        self.save_textual_summary(results_df, df, len(X_train), len(X_test), output_dir, sentiment_dist, df_all, cm_data)

        return results

    def save_textual_summary(self, results_df, dataset_df, train_size, test_size, output_dir, sentiment_dist, full_df, cm_data):
        summary_path = os.path.join(output_dir, "evaluation_summary.txt")
        dist = dataset_df['label'].value_counts().to_dict()

        # Full 3-class distribution from lexicon labeling (tujuan 1)
        full_dist = full_df['label'].value_counts().to_dict()
        total_all = len(full_df)
        label_id = {"positive": "Positif", "negative": "Negatif", "neutral": "Netral"}
        full_dist_lines = "\n".join(
            f"- {label_id[lbl]:<8}: {full_dist.get(lbl, 0)} tweet ({full_dist.get(lbl, 0) / total_all * 100:.1f}%)"
            for lbl in ["positive", "negative", "neutral"]
        )
        dominant_label = max(full_dist, key=full_dist.get)
        dominant_pct_all = full_dist[dominant_label] / total_all * 100
        neutral_count = full_dist.get('neutral', 0)

        # Calculate summary metrics
        nb_acc = results_df.loc["Naive Bayes", "Accuracy"]
        svm_acc = results_df.loc["SVM", "Accuracy"]

        # Confusion matrix breakdown per model on test data (tujuan 2 & 3)
        cm_lines = []
        for model_name, cm in cm_data.items():
            tn, fp, fn, tp = cm.ravel()
            cm_lines.append(
                f"- {model_name} (data uji = {test_size} tweet):\n"
                f"  True Negative (Negatif benar ditebak Negatif)  : {tn} tweet\n"
                f"  False Positive (Negatif salah ditebak Positif) : {fp} tweet\n"
                f"  False Negative (Positif salah ditebak Negatif) : {fn} tweet\n"
                f"  True Positive (Positif benar ditebak Positif)  : {tp} tweet\n"
                f"  >> Total prediksi benar: {tn + tp} dari {test_size} tweet ({(tn + tp) / test_size * 100:.1f}%)"
            )
        cm_section = "\n\n".join(cm_lines)

        # Determine the most effective algorithm (tujuan 4) by counting metric wins
        metric_cols = ["Accuracy", "Precision", "Recall", "F1-Score"]
        nb_wins = sum(results_df.loc["Naive Bayes", m] > results_df.loc["SVM", m] for m in metric_cols)
        svm_wins = sum(results_df.loc["SVM", m] > results_df.loc["Naive Bayes", m] for m in metric_cols)
        if nb_wins == svm_wins:
            best_model_line = ("Kedua algoritma menunjukkan performa yang seimbang "
                               f"({nb_wins} vs {svm_wins} metrik unggul), sehingga belum dapat ditentukan "
                               "algoritma yang paling efektif pada dataset saat ini.")
        else:
            winner = "SVM (Linear Kernel)" if svm_wins > nb_wins else "Naive Bayes"
            best_model_line = (f"Algoritma paling efektif: {winner}, unggul pada "
                               f"{max(nb_wins, svm_wins)} dari {len(metric_cols)} metrik evaluasi "
                               "(accuracy, precision, recall, F1-score).")

        # Build per-model public sentiment conclusion lines
        sentiment_lines = []
        for model_name, counts in sentiment_dist.items():
            total = counts["positive"] + counts["negative"]
            pos_pct = counts["positive"] / total * 100 if total else 0
            neg_pct = counts["negative"] / total * 100 if total else 0
            dominant = "POSITIF" if counts["positive"] > counts["negative"] else "NEGATIF"
            dominant_pct = max(pos_pct, neg_pct)
            sentiment_lines.append(
                f"- {model_name}:\n"
                f"  Positif : {counts['positive']} tweet ({pos_pct:.1f}%)\n"
                f"  Negatif : {counts['negative']} tweet ({neg_pct:.1f}%)\n"
                f"  >> Kesimpulan: Respon publik terhadap MBG dominan {dominant} ({dominant_pct:.1f}%) menurut model {model_name}."
            )
        sentiment_section = "\n\n".join(sentiment_lines)

        # Build the text file content
        content = f"""======================================================================
LAPORAN EVALUASI MODEL: NAIVE BAYES VS SUPPORT VECTOR MACHINE (SVM)
======================================================================
Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Output directory: {output_dir}/

1. RINGKASAN DATASET & DISTRIBUSI
----------------------------------------------------------------------
a. Distribusi Sentimen Hasil Pelabelan (Tujuan 1: Kecenderungan Sentimen)
Total tweet berlabel: {total_all} tweet
{full_dist_lines}
>> Kecenderungan sentimen masyarakat terhadap Program MBG berdasarkan
   pelabelan data dari media sosial X: dominan {label_id[dominant_label].upper()} ({dominant_pct_all:.1f}%).

b. Dataset Klasifikasi Model (Excluding neutral tweets)
Total tweet yang diuji: {len(dataset_df)} tweet
- Jumlah Kelas Positif: {dist.get('positive', 0)} tweet
- Jumlah Kelas Negatif: {dist.get('negative', 0)} tweet
- Jumlah Data Training (80%): {train_size} tweet
- Jumlah Data Testing (20%): {test_size} tweet

2. MATRIKS PERFORMA KLASIFIKASI
----------------------------------------------------------------------
{results_df.to_markdown()}

3. HASIL PENERAPAN MASING-MASING ALGORITMA (CONFUSION MATRIX)
----------------------------------------------------------------------
Rincian hasil klasifikasi tiap algoritma pada data uji
(Tujuan 2: Penerapan Naive Bayes | Tujuan 3: Penerapan SVM):

{cm_section}

4. DEFINISI & CARA MEMBACA METRIK
----------------------------------------------------------------------
- ACCURACY  : Persentase jawaban benar secara keseluruhan.
              Contoh: Akurasi {svm_acc:.2f} berarti model menebak {svm_acc*100:.1f}% data uji dengan benar.
- PRECISION : Dari semua tweet yang ditebak positif oleh model, berapa % yang aslinya positif.
- RECALL    : Dari semua tweet yang aslinya positif, berapa % yang berhasil dideteksi oleh model.
- F1-SCORE  : Rata-rata harmonis Presisi dan Recall (keseimbangan tebakan model).
- AUC-ROC   : Mengukur kemampuan pemisahan kelas sentimen (rentang 0.5 s.d 1.0).
              Nilai > 0.7 menunjukkan model pemisahan yang kuat/baik.

5. ANALISIS DAN PERBANDINGAN METODE (Tujuan 4: Algoritma Paling Efektif)
----------------------------------------------------------------------
- Naive Bayes Accuracy : {nb_acc * 100:.2f}%
- SVM (Linear) Accuracy : {svm_acc * 100:.2f}%

* Analisis Hasil:
{"Kedua model memiliki tingkat akurasi yang sama karena keterbatasan jumlah data uji saat ini. Model menebak pola yang mirip." if abs(nb_acc - svm_acc) < 1e-4 else ("SVM mengungguli Naive Bayes dari sisi akurasi, yang sejalan dengan temuan riset pada data besar (Article.pdf)." if svm_acc > nb_acc else "Naive Bayes mengungguli SVM dari sisi akurasi pada dataset saat ini. Perbandingan menyeluruh (termasuk Recall, F1-Score, dan AUC-ROC) dapat dilihat pada Kesimpulan Perbandingan di bawah.")}

* Kesimpulan Perbandingan:
{best_model_line}

* Keterbatasan (Class Imbalance):
Distribusi data yang didominasi oleh kelas mayoritas mempengaruhi nilai Recall. Direkomendasikan untuk menambah variasi tweet unik guna melatih model agar lebih peka terhadap kelas minoritas.

6. KESIMPULAN SENTIMEN PUBLIK TERHADAP PROGRAM MBG
----------------------------------------------------------------------
Prediksi sentimen dilakukan pada seluruh dataset berlabel ({sum(sentiment_dist["Naive Bayes"].values())} tweet)
menggunakan masing-masing model yang telah dilatih:

{sentiment_section}

* Catatan Metodologi:
Kedua model dilatih secara biner (positif vs negatif) mengikuti metodologi
penelitian JATI, sehingga model tidak dapat memprediksi kelas netral.
Berdasarkan pelabelan manual (lexicon), terdapat {neutral_count} tweet netral
yang dikecualikan dari klasifikasi model.
======================================================================
"""
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Textual evaluation report saved to '{summary_path}'")

    def compute_metrics(self, y_true, y_pred, y_probs):
        accuracy = accuracy_score(y_true, y_pred)
        # Use zero_division parameter to handle cases where negative class is never predicted
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        try:
            auc = roc_auc_score(y_true, y_probs)
        except ValueError:
            auc = 0.0 # if only one class exists in test set or probabilities are constant
            
        return {
            "Accuracy": accuracy,
            "Precision": precision,
            "Recall": recall,
            "F1-Score": f1,
            "AUC-ROC": auc
        }

    def save_confusion_matrix(self, y_true, y_pred, model_name, dest_path):
        cm = confusion_matrix(y_true, y_pred)
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Negative", "Positive"])
        fig, ax = plt.subplots(figsize=(6, 5))
        disp.plot(cmap=plt.cm.Blues, ax=ax)
        ax.set_title(f"Confusion Matrix: {model_name}")
        plt.tight_layout()
        plt.savefig(dest_path)
        plt.close()

    def plot_comparison(self, df, dest_path):
        # Transpose to group by metric instead of model
        plot_df = df.T
        
        fig, ax = plt.subplots(figsize=(10, 6))
        plot_df.plot(kind="bar", ax=ax, rot=0)
        ax.set_title("Performance Comparison: Naive Bayes vs SVM")
        ax.set_ylabel("Score")
        ax.set_ylim(0, 1.05)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        plt.legend(loc="lower right")
        plt.tight_layout()
        plt.savefig(dest_path)
        plt.close()
