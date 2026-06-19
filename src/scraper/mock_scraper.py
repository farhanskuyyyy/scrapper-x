import random
from datetime import datetime, timedelta
from src.scraper.base_scraper import BaseScraper

class MockScraper(BaseScraper):
    def __init__(self):
        # Sample templates to generate realistic-looking tweets
        self.pos_templates = [
            "Sangat setuju dengan program Makan Bergizi Gratis (MBG), ini sangat membantu meningkatkan gizi anak sekolah biar pintar dan sehat!",
            "Mantap sekali program makan bergizi gratis ini! Semoga lancar terus pelaksanaannya untuk Indonesia Emas 2045.",
            "Alhamdulillah anak saya senang sekali dapat makan siang sehat dan gratis di sekolah. Terima kasih pemerintah.",
            "Program MBG ini luar biasa bagus sekali untuk masa depan bangsa, terutama bagi anak-anak di daerah pelosok.",
            "Mendukung penuh kebijakan makan bergizi gratis. Ini adalah investasi jangka panjang untuk kualitas SDM kita.",
            "Terima kasih atas pelaksanaan makan bergizi gratis yang sukses, makanannya bergizi dan rasanya enak kata anak saya.",
            "Ini program yang sangat dinanti, sangat bermanfaat sekali bagi masyarakat kecil yang kesulitan memenuhi kebutuhan gizi.",
            "Semoga program Makan Bergizi Gratis berjalan sukses dan merata di seluruh wilayah Indonesia.",
            "Program makan bergizi gratis membantu sekali meringankan beban pengeluaran uang belanja harian kami.",
            "Hebat! Makanannya dikemas bersih, porsinya pas, dan anak-anak jadi lebih semangat belajar dengan adanya MBG."
        ]
        
        self.neg_templates = [
            "Khawatir sekali dengan anggaran Makan Bergizi Gratis yang sangat besar ini, rawan korupsi kalau tidak diawasi ketat.",
            "Program MBG ini tampaknya kurang tepat sasaran, mending anggarannya dipakai buat perbaikan sekolah yang rusak.",
            "Uji coba makan bergizi gratis kemarin makanannya kurang higienis, ada anak yang sakit perut setelah makan.",
            "Makan bergizi gratis ini boros anggaran negara saja, kasihan utang negara makin menumpuk demi program ini.",
            "Saya tidak yakin program mbg bisa merata dan adil di daerah terpencil. Rawan dimanfaatkan oknum nakal.",
            "Kualitas makanan uji coba mbg sangat buruk dan porsinya sedikit sekali, tidak sesuai dengan anggaran yang dipublikasikan.",
            "Lebih baik fokus meningkatkan kualitas guru daripada program makan bergizi gratis yang berisik ini.",
            "Aduuh pelaksanaannya kacau, pembagian makan siang gratis di sekolah kami kemarin berantakan sekali.",
            "Makan bergizi gratis cuma janji politik yang dipaksakan, kasihan anggaran negara terbebani.",
            "Khawatir kualitas gizi makanannya menurun setelah program ini berjalan lama karena anggarannya dipotong di jalan."
        ]
        
        self.neu_templates = [
            "Bagaimana perkembangan pelaksanaan uji coba program Makan Bergizi Gratis di daerah kalian masing-masing?",
            "Hari ini ada rapat sosialisasi mengenai petunjuk teknis pelaksanaan program MBG oleh dinas pendidikan.",
            "Uji coba makan bergizi gratis sudah mulai dilaksanakan di beberapa sekolah dasar di Jawa Barat.",
            "Dinas kesehatan setempat sedang memeriksa kandungan gizi menu makanan untuk program makan bergizi gratis besok.",
            "Pemerintah terus mematangkan skema distribusi makanan untuk mensukseskan program MBG tahun ini.",
            "Apakah program Makan Bergizi Gratis ini juga berlaku untuk anak-anak sekolah swasta di kota besar?",
            "Rencana anggaran untuk program MBG terus dibahas secara intensif di DPR minggu ini."
        ]
        
        self.usernames = ["budi_santoso", "siti_aminah", "andi_wijaya", "dewi_lestari", "eko_prabowo", 
                          "rudi_hermawan", "ani_puspita", "wawan_kristian", "diana_putri", "hendra_gunawan",
                          "mega_sari", "ridwan_hakim", "lestari_wulandari", "agus_priyanto", "kartika_sari"]

    def search_tweets(self, query, limit=100):
        tweets = []
        now = datetime.now()
        
        # We generate a mix of positive (mostly, around 85-90% as seen in the article), 
        # negative (around 8-10%), and neutral (2-5%) tweets
        for i in range(limit):
            rand = random.random()
            if rand < 0.85:
                text = random.choice(self.pos_templates)
            elif rand < 0.95:
                text = random.choice(self.neg_templates)
            else:
                text = random.choice(self.neu_templates)
                
            # Randomize some details to make tweets look unique
            tweet_id = str(random.randint(1000000000000000000, 9999999999999999999))
            username = random.choice(self.usernames) + str(random.randint(1, 99))
            # Random date within last 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 23)
            minutes_ago = random.randint(0, 59)
            tweet_date = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            reply_to = str(random.randint(1000000000000000000, 9999999999999999999)) if random.random() < 0.3 else None
            tweets.append({
                'tweet_id': tweet_id,
                'username': username,
                'created_at': tweet_date.isoformat(),
                'raw_text': text,
                'keyword': query,
                'reply_to_id': reply_to
            })
            
        return tweets
