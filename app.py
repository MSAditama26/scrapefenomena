import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def get_tanggal_detail(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # PRIORITAS 1: meta tag
        meta = soup.find("meta", property="article:published_time")
        if meta and meta.get("content"):
            dt = datetime.fromisoformat(
                meta["content"].replace("Z", "")
            )
            return dt.replace(tzinfo=None)  # ⬅️ FIX UTAMA

        # PRIORITAS 2: tag <time>
        time_tag = soup.find("time")
        if time_tag:
            if time_tag.get("datetime"):
                dt = datetime.fromisoformat(
                    time_tag["datetime"].split("T")[0]
                )
                return dt.replace(tzinfo=None)
            else:
                return parse_tanggal_indonesia(time_tag.get_text())

        return None
    except:
        return None

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # PRIORITAS 1: meta tag
        meta = soup.find("meta", property="article:published_time")
        if meta and meta.get("content"):
            return datetime.fromisoformat(
                meta["content"].replace("Z", "")
            )

        # PRIORITAS 2: tag <time>
        time_tag = soup.find("time")
        if time_tag:
            if time_tag.get("datetime"):
                return datetime.fromisoformat(
                    time_tag["datetime"].split("T")[0]
                )
            else:
                return parse_tanggal_indonesia(time_tag.get_text())

        return None
    except:
        return None


def parse_tanggal_indonesia(text):
    bulan = {
        "januari": "01",
        "februari": "02",
        "maret": "03",
        "april": "04",
        "mei": "05",
        "juni": "06",
        "juli": "07",
        "agustus": "08",
        "september": "09",
        "oktober": "10",
        "november": "11",
        "desember": "12"
    }

    try:
        parts = text.lower().split()
        if len(parts) < 3:
            return None

        hari = parts[0]
        bulan_angka = bulan.get(parts[1])
        tahun = parts[2]

        if not bulan_angka:
            return None

        tanggal_str = f"{tahun}-{bulan_angka}-{hari.zfill(2)}"
        return datetime.strptime(tanggal_str, "%Y-%m-%d")
    except:
        return None


# =========================
# FUNGSI SCRAPING
# =========================
def scrape_berita(url, keyword, start_date, end_date):
    headers = {"User-Agent": "Mozilla/5.0"}
    soup = BeautifulSoup(
        requests.get(url, headers=headers).text,
        "html.parser"
    )

    data = []

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        link = a["href"]

        if not title or len(title) < 20:
            continue
        if keyword.lower() not in title.lower():
            continue
        if not link.startswith("http"):
            continue

        tanggal_obj = get_tanggal_detail(link)

        if tanggal_obj:
            if not (start_date <= tanggal_obj <= end_date):
                continue
            tanggal_text = tanggal_obj.strftime("%Y-%m-%d")
        else:
            tanggal_text = ""

        data.append({
            "judul": title,
            "url": link,
            "tanggal": tanggal_text,
            "keyword": keyword
        })

    return pd.DataFrame(data).drop_duplicates("url")


# =========================
# STREAMLIT UI
# =========================
st.set_page_config(page_title="Scraping Berita", layout="wide")

st.title("📰 Web Scraping Berita")
st.write("Mengambil **judul, URL, dan tanggal** berita berdasarkan **keyword**")

st.subheader("Filter")

start_date = st.date_input("Tanggal awal")
end_date = st.date_input("Tanggal akhir")


url = st.text_input(
    "URL halaman berita",
    placeholder="contoh: https://www.antaranews.com/ekonomi"
)

keyword = st.text_input(
    "Keyword",
    placeholder="contoh: inflasi"
)

if st.button("🔍 Scrape Berita"):
    if not url or not keyword:
        st.warning("URL dan keyword wajib diisi")
    else:
        with st.spinner("Sedang mengambil data..."):
            try:
                df = scrape_berita(
    url,
    keyword,
    datetime.combine(start_date, datetime.min.time()),
    datetime.combine(end_date, datetime.max.time())
)


                if df.empty:
                    st.warning("Tidak ada berita yang sesuai keyword")
                else:
                    st.success(f"Ditemukan {len(df)} berita")
                    st.dataframe(df, use_container_width=True)

                    # =========================
                    # EXPORT EXCEL
                    # =========================
                    tanggal_run = datetime.now().strftime("%Y%m%d_%H%M")
                    nama_file = f"berita_{keyword}_{tanggal_run}.xlsx"

                    df.to_excel(nama_file, index=False)

                    with open(nama_file, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Excel",
                            data=f,
                            file_name=nama_file,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

            except Exception as e:
                st.error(f"Terjadi error: {e}")
