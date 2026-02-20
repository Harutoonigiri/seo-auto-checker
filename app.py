import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

st.set_page_config(
    page_title="SEO自動チェッカー",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 SEO自動判定・改善システム")
st.markdown("URLを入力するだけでSEOの問題点を自動検出し、改善提案を行います。")

# --- 入力フォーム ---
with st.form(key="seo_form"):
    url_input = st.text_input(
        "チェックするURL",
        placeholder="https://example.com",
        help="SEOをチェックしたいWebページのURLを入力してください"
    )
    submit = st.form_submit_button("🚀 SEOチェック開始")

if submit and url_input:
    # URLのバリデーション
    if not url_input.startswith(("http://", "https://")):
        url_input = "https://" + url_input

    with st.spinner("ページを取得してSEO分析中..."):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; SEOChecker/1.0)"
            }
            response = requests.get(url_input, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            st.error(f"ページの取得に失敗しました: {e}")
            st.stop()

    st.success(f"取得完了: {url_input}")
    st.divider()

    # --- チェック項目 ---
    results = []

    # 1. titleタグ
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    title_len = len(title_text)
    if not title_text:
        results.append({"category": "title", "status": "❌", "item": "titleタグ", "detail": "titleタグが存在しません", "fix": "<title>ページタイトル</title> を追加してください"})
    elif title_len < 20:
        results.append({"category": "title", "status": "⚠️", "item": "titleタグ", "detail": f"titleが短すぎます（{title_len}文字）", "fix": "20〜60文字程度のキーワードを含む説明的なタイトルにしましょう"})
    elif title_len > 60:
        results.append({"category": "title", "status": "⚠️", "item": "titleタグ", "detail": f"titleが長すぎます（{title_len}文字）", "fix": "60文字以内に収めてください。検索結果で切れてしまいます"})
    else:
        results.append({"category": "title", "status": "✅", "item": "titleタグ", "detail": f"良好（{title_len}文字）: {title_text[:50]}", "fix": ""})

    # 2. meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc_text = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""
    desc_len = len(desc_text)
    if not desc_text:
        results.append({"category": "meta", "status": "❌", "item": "meta description", "detail": "meta descriptionが存在しません", "fix": '<meta name="description" content="ページの説明文"> を追加してください'})
    elif desc_len < 50:
        results.append({"category": "meta", "status": "⚠️", "item": "meta description", "detail": f"descriptionが短すぎます（{desc_len}文字）", "fix": "50〜160文字程度の説明文を書きましょう"})
    elif desc_len > 160:
        results.append({"category": "meta", "status": "⚠️", "item": "meta description", "detail": f"descriptionが長すぎます（{desc_len}文字）", "fix": "160文字以内に収めてください"})
    else:
        results.append({"category": "meta", "status": "✅", "item": "meta description", "detail": f"良好（{desc_len}文字）", "fix": ""})

    # 3. H1タグ
    h1_tags = soup.find_all("h1")
    h1_count = len(h1_tags)
    if h1_count == 0:
        results.append({"category": "heading", "status": "❌", "item": "H1タグ", "detail": "H1タグが存在しません", "fix": "ページのメインキーワードを含む <h1> タグを1つ追加してください"})
    elif h1_count > 1:
        results.append({"category": "heading", "status": "⚠️", "item": "H1タグ", "detail": f"H1タグが複数あります（{h1_count}個）", "fix": "H1タグは1ページに1つが原則です"})
    else:
        results.append({"category": "heading", "status": "✅", "item": "H1タグ", "detail": f"良好: {h1_tags[0].get_text(strip=True)[:50]}", "fix": ""})

    # 4. 画像のalt属性
    images = soup.find_all("img")
    img_no_alt = [img for img in images if not img.get("alt")]
    if img_no_alt:
        results.append({"category": "image", "status": "⚠️", "item": "画像のalt属性", "detail": f"{len(img_no_alt)}個の画像にalt属性がありません", "fix": "すべての <img> タグに適切な alt 属性を追加してください"})
    elif images:
        results.append({"category": "image", "status": "✅", "item": "画像のalt属性", "detail": f"すべての画像（{len(images)}個）にaltが設定されています", "fix": ""})
    else:
        results.append({"category": "image", "status": "ℹ️", "item": "画像のalt属性", "detail": "画像が見つかりませんでした", "fix": ""})

    # 5. canonical タグ
    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical:
        results.append({"category": "technical", "status": "✅", "item": "canonicalタグ", "detail": f"設定済み: {canonical.get('href', '')[:60]}", "fix": ""})
    else:
        results.append({"category": "technical", "status": "⚠️", "item": "canonicalタグ", "detail": "canonicalタグがありません", "fix": '<link rel="canonical" href="URL"> を <head> 内に追加してください'})

    # 6. OGPタグ
    og_title = soup.find("meta", property="og:title")
    og_desc = soup.find("meta", property="og:description")
    og_image = soup.find("meta", property="og:image")
    ogp_ok = all([og_title, og_desc, og_image])
    if ogp_ok:
        results.append({"category": "social", "status": "✅", "item": "OGPタグ", "detail": "og:title / og:description / og:image がすべて設定されています", "fix": ""})
    else:
        missing = []
        if not og_title: missing.append("og:title")
        if not og_desc: missing.append("og:description")
        if not og_image: missing.append("og:image")
        results.append({"category": "social", "status": "⚠️", "item": "OGPタグ", "detail": f"不足: {', '.join(missing)}", "fix": "SNSシェア時の見た目のために OGP タグを追加しましょう"})

    # --- 結果表示 ---
    ok_count = sum(1 for r in results if r["status"] == "✅")
    warn_count = sum(1 for r in results if r["status"] == "⚠️")
    ng_count = sum(1 for r in results if r["status"] == "❌")

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ OK", ok_count)
    col2.metric("⚠️ 警告", warn_count)
    col3.metric("❌ NG", ng_count)

    st.subheader("📊 チェック結果")
    for r in results:
        with st.expander(f"{r['status']} {r['item']} — {r['detail'][:60]}"):
            st.markdown(f"**詳細:** {r['detail']}")
            if r["fix"]:
                st.markdown(f"**改善提案:** {r['fix']}")

elif submit:
    st.warning("URLを入力してください。")
