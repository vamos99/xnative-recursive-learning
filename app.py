"""
app.py
------

This module defines a Streamlit web application for interacting with the
XNative Recursive Learning project. It allows end‑users to fetch
recent posts for a given keyword, summarise and translate them on the
fly, and track progress through an integrated project board.

To launch the application run::

    streamlit run app.py

The UI is intentionally minimalist: the left sidebar contains inputs for
scraping and summarisation parameters, while the main area displays
results and the current project board. Feel free to customise
styling and additional features.

Notes
-----
* The summariser and translator require optional dependencies
  (``transformers`` and ``googletrans`` respectively). If these
  dependencies are missing the app will still run but summarisation and
  translation will fall back to no‑op implementations.
* The board is stored in ``board.json`` in the current working
  directory by default. When you run multiple instances of the app they
  will share the same board state.
"""

from __future__ import annotations

import streamlit as st
from pathlib import Path
from typing import Optional, List

from .trending import get_posts
from .summarizer import summarize
from .translator import translate, is_translation_available
from .board import ProjectBoard


def run_app() -> None:
    st.set_page_config(page_title="XNative Recursive Learning", layout="wide")
    st.title("XNative Recursive Learning")
    st.write(
        "Bu uygulama Twitter/X üzerinden anahtar kelime araması yapar, "
        "toplanan gönderileri özetler ve çeviri hizmetleri sunar. Aynı zamanda "
        "projeye ait görevlerin takibini sağlayan bir pano içerir."
    )

    board_file = Path(st.sidebar.text_input("Board dosya adı", value="board.json"))
    board = ProjectBoard(board_file)

    st.sidebar.header("Arama ve Özetleme Ayarları")
    keyword = st.sidebar.text_input("Anahtar kelime / hashtag", value="yapay zeka")
    limit = st.sidebar.slider("Gönderi sayısı", min_value=1, max_value=50, value=10)
    lang = st.sidebar.text_input("Dil kodu", value="tr")
    sum_min = st.sidebar.slider("Özet min uzunluğu", min_value=10, max_value=100, value=40)
    sum_max = st.sidebar.slider("Özet max uzunluğu", min_value=50, max_value=300, value=150)
    translate_lang: Optional[str] = st.sidebar.text_input("Çeviri dili (boş bırakırsan çevrilmez)", value="en")

    if st.sidebar.button("Gönderileri Getir"):
        with st.spinner("Gönderiler indiriliyor..."):
            posts = get_posts(keyword, limit=limit, lang=lang)
        if not posts:
            st.warning("Belirtilen anahtar kelime için gönderi bulunamadı veya tarayıcı modülü yüklenemedi.")
        else:
            # Display posts in an expander
            for idx, post in enumerate(posts, start=1):
                with st.expander(f"Gönderi {idx} (by @{post.user})"):
                    st.write(post.content)
                    summary = summarize(post.content, max_length=sum_max, min_length=sum_min)
                    st.markdown("**Özet:**")
                    st.write(summary)
                    if translate_lang and is_translation_available():
                        translation = translate(summary, target_lang=translate_lang)
                        st.markdown(f"**Çeviri ({translate_lang}):**")
                        st.write(translation)
                    st.markdown(f"[Gönderi linki]({post.url})")
            # Log this action on the board
            board.add_task(
                title=f"Scraped posts for '{keyword}'",
                description=f"Fetched {len(posts)} posts and generated summaries via UI",
                status="done",
            )
            st.success("Görev pano'ya kaydedildi.")

    st.header("Proje Panosu")
    tasks = board.list_tasks()
    if not tasks:
        st.info("Panoda görev bulunmuyor.")
    else:
        for task in tasks:
            cols = st.columns([1, 3, 2])
            cols[0].markdown(f"**#{task.id}**")
            cols[1].markdown(f"**{task.title}**\n{task.description}")
            # Editable status
            new_status = cols[2].selectbox(
                "Durum", options=["todo", "in_progress", "done"], index=["todo", "in_progress", "done"].index(task.status), key=f"status_{task.id}"
            )
            if new_status != task.status:
                board.update_task(task.id, status=new_status)
                st.experimental_rerun()

    st.sidebar.header("Görev Ekle")
    new_title = st.sidebar.text_input("Başlık", key="new_task_title")
    new_desc = st.sidebar.text_area("Açıklama", key="new_task_desc")
    new_status = st.sidebar.selectbox("Durum", options=["todo", "in_progress", "done"], key="new_task_status")
    if st.sidebar.button("Görev Oluştur"):
        if not new_title:
            st.sidebar.error("Görev başlığı boş bırakılamaz.")
        else:
            board.add_task(new_title, description=new_desc, status=new_status)
            st.sidebar.success("Yeni görev eklendi!")
            st.experimental_rerun()


if __name__ == "__main__":
    run_app()
