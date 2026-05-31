"""
Streamlit Demo — GPT Halüsinasyonlarının Ontoloji Tabanlı Yöntemlerle Önlenmesi

Çalıştırma:
    streamlit run app/main.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Streamlit dosyayı doğrudan çalıştırırken proje kökünü PYTHONPATH'e ekle
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
from dotenv import load_dotenv

from app.hallucination_detector import (
    ClaimStatus,
    HallucinationDetector,
    VerifiedClaim,
)
from app.llm_client import LLMClient
from app.ontology_engine import OntologyEngine, UniversityFacts

load_dotenv()

# ---------------------------------------------------------------- sayfa kurulumu
st.set_page_config(
    page_title="Ontoloji Tabanlı Halüsinasyon Önleme",
    page_icon="🧠",
    layout="wide",
)

# ---------------------------------------------------------------- önbellekli motorlar
@st.cache_resource(show_spinner="Ontoloji yükleniyor…")
def get_ontology() -> OntologyEngine:
    return OntologyEngine()


def get_llm() -> LLMClient | None:
    api_key = st.session_state.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        return LLMClient(api_key=api_key)
    except Exception as e:  # noqa: BLE001
        st.sidebar.error(f"LLM başlatılamadı: {e}")
        return None


# ---------------------------------------------------------------- yardımcılar
def render_facts_block(facts: list[UniversityFacts]) -> str:
    if not facts:
        return "(Soruda ontolojide tanımlı bir üniversite tespit edilmedi.)"
    return "\n\n".join(f.as_natural_text() for f in facts)


def render_verified_table(verified: list[VerifiedClaim]) -> None:
    if not verified:
        st.caption("Cevaptan yapısal bir olgu iddiası çıkarılamadı.")
        return
    rows = []
    for v in verified:
        rows.append({
            "Durum": f"{v.emoji} {v.status.value}",
            "Üniversite": v.university,
            "Özellik": v.humanize_property(),
            "İddia edilen": v.claimed_value,
            "Ontolojideki gerçek": v.actual_value or "—",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def _ontology_prompt_preview(ontology_context: str) -> str:
    """ask_with_ontology'de kullanılan sistem promptunun birebir önizlemesi."""
    return (
        "Sen Türkiye üniversiteleri hakkında soruları SADECE ve SADECE "
        "aşağıdaki 'DOĞRULANMIŞ ONTOLOJİ OLGULARI' bölümünde verilen bilgilere "
        "dayanarak cevaplayan bir asistansın.\n\n"
        "KESİN KURALLAR:\n"
        "1. Ontolojide olmayan bilgi için 'Ontolojide bu bilgi bulunmuyor' de.\n"
        "2. ASLA varsayım yapma, tahmin etme, genel bilgi kullanma.\n"
        "3. Ontolojideki sayı/şehir/yıl/isim bilgilerini değiştirmeden kullan.\n"
        "4. Cevabını kaynak gösterecek şekilde yaz: '(Ontoloji: …)' formatında.\n"
        "5. Türkçe yanıtla, kısa ve net ol.\n\n"
        "DOĞRULANMIŞ ONTOLOJİ OLGULARI:\n"
        f"{ontology_context if ontology_context.strip() else '(Bu soruyla ilgili eşleşen olgu yok.)'}"
    )


def render_how_it_works(onto: OntologyEngine) -> None:
    """Sistemi hiç bilmeyen birine uygulamalı olarak gösteren rehber."""
    st.header("📖 Sistem Nasıl Çalışıyor?")
    st.markdown(
        "Bu uygulama, **GPT'nin uydurma (halüsinasyon) yapma eğilimini** "
        "**doğrulanmış bir bilgi grafiğine (ontoloji)** dayandırarak azaltır. "
        "Aşağıdaki 5 adımı sırayla okuyun; son adımda kendiniz deneyebilirsiniz."
    )

    # --- 1) Problem ---
    with st.container(border=True):
        st.subheader("1️⃣ Problem: GPT İkna Edici Şekilde Uydurabilir")
        st.markdown(
            "Saf bir LLM'e *“Sabancı Üniversitesi 1999 yılında Ankara'da kuruldu, "
            "doğru mu?”* diye sorduğunuzda model, **eğitim verisinden hatırladığını sandığı** "
            "bilgilerle cevap üretir. Yıllar/şehirler/türler arasında karışıklıklar olabilir. "
            "Üstelik **özgüvenli** ve **kaynaksız** cevap verir – yanlış olduğunu "
            "kullanıcının fark etmesi zordur."
        )
        st.info("Hedef: cevabı **yalnızca doğrulanmış olgulara** dayandırmak.")

    # --- 2) Ontoloji ---
    with st.container(border=True):
        st.subheader("2️⃣ Çözüm: Doğrulanmış Olgular (Ontoloji)")
        st.markdown(
            "Türk üniversitelerini **RDF/Turtle** formatında bir bilgi grafiğinde "
            "modelliyoruz. Her üniversite için kuruluş yılı, şehir, tür (devlet/vakıf) "
            "ve fakülteler gibi olgular yapısal olarak tanımlıdır."
        )
        st.code(
            """uni:ESOGU a uni:PublicUniversity ;
    rdfs:label "Eskişehir Osmangazi Üniversitesi"@tr ;
    uni:officialName "Eskişehir Osmangazi Üniversitesi" ;
    uni:foundedYear 1993 ;
    uni:locatedIn uni:Eskisehir ;
    uni:hasFaculty uni:F_Tip, uni:F_Muh, uni:F_Mim,
                   uni:F_FenEd, uni:F_Iibf, uni:F_Egitim ;
    uni:website "https://www.ogu.edu.tr"^^xsd:anyURI .""",
            language="turtle",
        )
        st.caption(
            f"Şu an ontolojide **{len(onto.all_universities())} üniversite** tanımlı. "
            "Tam liste için yan paneldeki '📖 Ontolojideki üniversiteler' bölümüne bakın."
        )

    # --- 3) Boru hattı ---
    with st.container(border=True):
        st.subheader("3️⃣ Boru Hattı: Sorudan Doğrulanmış Cevaba")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("**1. Tanı**")
            st.caption(
                "Sorudaki üniversite isimlerini/kısaltmalarını tanı "
                "(takma ad indeksi: 'ESOGÜ', 'Osmangazi', 'ODTÜ'…)."
            )
        with c2:
            st.markdown("**2. Çek**")
            st.caption(
                "Tanınan her üniversite için SPARQL ile olguları çek "
                "(yıl, şehir, tür, fakülteler)."
            )
        with c3:
            st.markdown("**3. Sor**")
            st.caption(
                "GPT'ye SADECE bu olgularla sınırlı cevap vermesini söyle. "
                "Aynı soruyu bağlamsız GPT'ye de sor – karşılaştırma için."
            )
        with c4:
            st.markdown("**4. Doğrula**")
            st.caption(
                "Cevaptan yapısal iddialar (`üniversite, özellik, değer`) "
                "çıkar ve her birini ontolojiye karşı kontrol et."
            )

    # --- 4) Uygulamalı: Canlı entity tespiti + olgu çekimi ---
    with st.container(border=True):
        st.subheader("4️⃣ Şimdi Sıra Sizde — Canlı Deneme")
        st.markdown(
            "Aşağıya bir üniversite adı veya kısaltma yazın. Sistem, **LLM çağırmadan** "
            "şu adımları o anda işleyip size gösterecek: hangi varlığı tanıdı, "
            "ontolojiden hangi olguları çekti, GPT'ye gönderilecek prompt nasıl görünüyor."
        )
        sample = st.text_input(
            "Örnek soru / üniversite adı",
            value="ESOGÜ kaç yılında ve hangi şehirde kuruldu?",
            key="howto_sample",
        )

        if sample.strip():
            detected_uris = onto.detect_universities(sample)
            detected_facts = onto.facts_for_text(sample)

            st.markdown("**Adım 1 — Tanınan varlıklar:**")
            if detected_uris:
                st.write(
                    " · ".join(
                        f"`{str(u).rsplit('#', 1)[-1]}`" for u in detected_uris
                    )
                )
            else:
                st.warning(
                    "Bu metinde ontolojide tanımlı bir üniversite tanınmadı. "
                    "Bu durumda ontoloji destekli model 'bilgi yok' diyecek; "
                    "saf GPT muhtemelen halüsinasyon yapacaktır."
                )

            if detected_facts:
                st.markdown("**Adım 2 — Ontolojiden çekilen olgular:**")
                for f in detected_facts:
                    st.markdown(f.as_natural_text())

                st.markdown("**Adım 3 — GPT'ye gönderilecek sistem promptu:**")
                ctx = render_facts_block(detected_facts)
                st.code(_ontology_prompt_preview(ctx), language="text")

                st.caption(
                    "Saf GPT bu prompt'u görmez – o sadece soruyu görür ve "
                    "eğitim verisinden hatırladığını sandığı bilgilerle cevap üretir."
                )

    # --- 5) Doğrulama mantığı ---
    with st.container(border=True):
        st.subheader("5️⃣ Halüsinasyon Dedektörü")
        st.markdown(
            "GPT'nin döndürdüğü cümleler insan dilindedir, ama biz onlardan "
            "**yapısal iddialar** çıkarıp ontolojiye karşı tek tek doğrularız."
        )
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Cevaptan çıkarılan iddia (örnek):**")
            st.code(
                '{\n'
                '  "university": "Sabancı Üniversitesi",\n'
                '  "property": "foundedYear",\n'
                '  "value": "1999"\n'
                '}',
                language="json",
            )
        with col_b:
            st.markdown("**Ontolojiye karşı sonuç:**")
            st.markdown(
                "- Ontolojideki gerçek değer: **1994**\n"
                "- Karar: **❌ Çelişiyor**\n"
                "- Bu iddia kullanıcıya kırmızıyla raporlanır."
            )
        st.caption(
            "Aynı kontrol şehir ve tür (devlet/vakıf) iddiaları için de yapılır. "
            "Sonuçlar Demo sekmesinin altındaki tabloda görüntülenir."
        )

    st.success(
        "✅ Hazırsanız üst kısımdaki **🚀 Demo** sekmesine geçin ve "
        "yan paneldeki hazır sorulardan birini seçerek sistemi gerçek bir LLM "
        "çağrısıyla deneyin."
    )


def metric_strip(verified: list[VerifiedClaim], label: str) -> None:
    summary = HallucinationDetector.summary(verified)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{label} – Toplam iddia", len(verified))
    c2.metric("✅ Destekleniyor", summary[ClaimStatus.SUPPORTED.value])
    c3.metric("❌ Çelişiyor", summary[ClaimStatus.CONTRADICTED.value])
    c4.metric("❔ Doğrulanamadı", summary[ClaimStatus.UNKNOWN.value])


# ---------------------------------------------------------------- yan panel
def sidebar() -> None:
    st.sidebar.title("⚙️ Ayarlar")

    env_key = os.getenv("OPENAI_API_KEY", "")
    api_key = st.sidebar.text_input(
        "OpenAI API Anahtarı",
        type="password",
        value=st.session_state.get("api_key", env_key),
        help=".env dosyasındaki anahtar otomatik yüklenir. Buradan da girilebilir.",
    )
    st.session_state["api_key"] = api_key

    st.sidebar.divider()
    st.sidebar.subheader("📚 Hazır Sorular")
    examples = [
        "Boğaziçi Üniversitesi hangi yıl kuruldu ve nerede?",
        "Sabancı Üniversitesi 1999 yılında Ankara'da kuruldu, doğru mu?",
        "Marmara Üniversitesi 1982 yılında İstanbul'da kuruldu, doğru mu?",
        "Boğaziçi Üniversitesi 1971 yılında mı kuruldu?",
        "Hacettepe Üniversitesi 1954 yılında mı kuruldu?",
    ]
    for q in examples:
        if st.sidebar.button(q, use_container_width=True, key=f"ex_{hash(q)}"):
            st.session_state["question"] = q

    st.sidebar.divider()
    with st.sidebar.expander("📖 Ontolojideki üniversiteler", expanded=False):
        onto = get_ontology()
        for f in onto.all_universities():
            st.markdown(
                f"- **{f.label}** · {f.founded_year} · {f.city} · {f.type_label}"
            )


# ---------------------------------------------------------------- ana akış
def main() -> None:
    sidebar()

    st.title("🧠 GPT Halüsinasyonlarının Ontoloji Tabanlı Yöntemlerle Önlenmesi")
    st.markdown(
        "Aynı soruyu **iki farklı şekilde** GPT'ye soruyoruz: "
        "(1) **bağlamsız** – halüsinasyon riski yüksek, "
        "(2) **ontoloji ile zenginleştirilmiş** – sadece doğrulanmış olgular."
    )

    onto = get_ontology()

    tab_demo, tab_how = st.tabs(["🚀 Demo", "📖 Nasıl Çalışıyor?"])

    with tab_how:
        render_how_it_works(onto)

    with tab_demo:
        run_demo_tab(onto)


def run_demo_tab(onto: OntologyEngine) -> None:
    question = st.text_area(
        "Sorunuzu yazın",
        value=st.session_state.get("question", ""),
        placeholder="Örn: Bilkent Üniversitesi 1980 yılında İzmir'de kurulmuş bir devlet üniversitesidir, doğru mudur?",
        height=90,
    )

    run = st.button("🚀 Karşılaştır", type="primary", use_container_width=True)

    if not run:
        st.info(
            "💡 Yan paneldeki hazır sorulardan birini seçebilir veya kendi sorunuzu yazabilirsiniz. "
            "Sistem, sorudaki üniversiteleri ontolojiden tespit edip karşılaştırma üretecektir."
        )
        return

    if not question.strip():
        st.warning("Lütfen bir soru girin.")
        return

    llm = get_llm()
    if llm is None:
        st.error(
            "OpenAI API anahtarı bulunamadı. Yan panelden anahtarınızı girin "
            "veya `.env` dosyasına ekleyin."
        )
        return

    # --- 1) Ontolojiden ilgili olgular ---
    detected_facts = onto.facts_for_text(question)
    detected_uris = [f.uri for f in detected_facts]
    ontology_context = render_facts_block(detected_facts)

    with st.expander("🔎 Ontolojiden çekilen olgular (RAG bağlamı)", expanded=False):
        if detected_facts:
            for f in detected_facts:
                st.markdown(f.as_natural_text())
            st.caption(
                f"Tespit edilen URI'ler: {', '.join(uri.rsplit('#',1)[-1] for uri in detected_uris)}"
            )
        else:
            st.warning(
                "Soruda tanınan bir üniversite yok. Ontoloji destekli model, "
                "elinde olgu olmadığı için 'bilgi yok' diyecek; saf GPT ise "
                "muhtemelen halüsinasyon yapacaktır."
            )

    # --- 2) İki yanıt ---
    left, right = st.columns(2, gap="large")

    with left:
        st.subheader("❌ Saf GPT (bağlamsız)")
        st.caption("Sadece eğitim verisindeki örtük bilgiyle cevap üretir – halüsinasyon riski.")
        with st.spinner("Saf GPT cevaplıyor…"):
            try:
                raw = llm.ask_raw(question)
            except Exception as e:  # noqa: BLE001
                st.error(f"Hata: {e}")
                return
        st.markdown(raw.text)

    with right:
        st.subheader("✅ Ontoloji Destekli GPT")
        st.caption("Sadece ontolojideki doğrulanmış olgulara dayanarak cevap verir.")
        with st.spinner("Ontoloji destekli GPT cevaplıyor…"):
            try:
                grounded = llm.ask_with_ontology(question, ontology_context)
            except Exception as e:  # noqa: BLE001
                st.error(f"Hata: {e}")
                return
        st.markdown(grounded.text)

    st.divider()
    st.subheader("🧪 Halüsinasyon Dedektörü — Yapısal Doğrulama")
    st.caption(
        "Her cevaptan olgu iddialarını (üniversite, özellik, değer) çıkarıp "
        "ontolojiye karşı tek tek doğruluyoruz."
    )

    detector = HallucinationDetector(onto)

    with st.spinner("İddialar çıkarılıyor ve doğrulanıyor…"):
        try:
            raw_claims = llm.extract_claims_json(raw.text)
            grounded_claims = llm.extract_claims_json(grounded.text)
        except Exception as e:  # noqa: BLE001
            st.error(f"İddia çıkarımında hata: {e}")
            return

        raw_verified = detector.verify_claims(raw_claims)
        grounded_verified = detector.verify_claims(grounded_claims)

    col_left, col_right = st.columns(2, gap="large")
    with col_left:
        st.markdown("**Saf GPT iddiaları**")
        metric_strip(raw_verified, "Saf GPT")
        render_verified_table(raw_verified)
    with col_right:
        st.markdown("**Ontoloji destekli iddialar**")
        metric_strip(grounded_verified, "Ontoloji+GPT")
        render_verified_table(grounded_verified)

    # --- karşılaştırma özeti ---
    st.divider()
    raw_summary = HallucinationDetector.summary(raw_verified)
    grd_summary = HallucinationDetector.summary(grounded_verified)
    raw_wrong = raw_summary[ClaimStatus.CONTRADICTED.value] + raw_summary[ClaimStatus.UNKNOWN.value]
    grd_wrong = grd_summary[ClaimStatus.CONTRADICTED.value] + grd_summary[ClaimStatus.UNKNOWN.value]

    if raw_wrong > grd_wrong:
        st.success(
            f"🎯 Sonuç: Ontoloji destekli model **{raw_wrong - grd_wrong} adet daha az "
            f"hatalı/doğrulanamayan iddia** üretti. Halüsinasyon başarıyla azaltıldı."
        )
    elif raw_wrong == grd_wrong == 0:
        st.info("İki model de bu soruda doğru iddialar üretti.")
    else:
        st.warning(
            "Bu soruda fark gözlemlenmedi. Daha çetrefilli (yıl/şehir karıştırılan) "
            "bir soru deneyin – yan paneldeki örnekler bu amaçla seçilmiştir."
        )


if __name__ == "__main__":
    main()
