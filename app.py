"""
求人マッチングWebアプリ (Streamlit版)
"""
import streamlit as st
import pandas as pd
from matching_logic import calculate_match_score, filter_results

# ページ設定
st.set_page_config(
    page_title="求人マッチングシステム",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSSでスタイル調整
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .job-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid #1f77b4;
    }
    .score-badge {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff6b6b;
    }
    .sub-score {
        font-size: 1rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# タイトル
st.markdown('<h1 class="main-header">🎯 求人マッチングシステム</h1>', unsafe_allow_html=True)

# サイドバー: 候補者情報入力フォーム
st.sidebar.header("📝 候補者情報入力")

with st.sidebar.form("candidate_form"):
    st.subheader("基本情報")
    name = st.text_input("名前", value="菊池 安梨沙")
    age = st.number_input("年齢", min_value=18, max_value=70, value=25)
    
    st.subheader("職務経歴")
    current_job = st.text_input("現在の職種", value="法人営業")
    years_exp = st.number_input("経験年数", min_value=0, max_value=50, value=3)
    
    skills_input = st.text_area(
        "スキル（改行区切りで入力）",
        value="法人営業\n新規開拓\n提案営業\n顧客フォロー\n関係者調整"
    )
    
    st.subheader("希望条件")
    desired_industry = st.text_input("希望業界", value="人材業界")
    
    desired_jobs_input = st.text_area(
        "希望職種（改行区切りで入力）",
        value="セールス\n法人営業\n採用コンサルタント"
    )
    
    desired_salary = st.number_input("希望年収（万円）", min_value=200, max_value=3000, value=450, step=50)
    
    location_options = ["東京都", "大阪府", "神奈川県", "愛知県", "福岡県", "その他"]
    desired_location = st.selectbox("希望勤務地", location_options, index=1)
    
    st.subheader("妥協可能なポイント")
    compromise_job = st.checkbox("職種", value=True)
    compromise_salary = st.checkbox("年収", value=True)
    compromise_location = st.checkbox("勤務地", value=False)
    
    aspiration = st.text_area(
        "志向性・キャリアビジョン",
        value="チームを大切にしながら企業の採用＋αに関わりたい。今後は採用だけでなく、企業の組織作りも行いたい。"
    )
    
    submit_button = st.form_submit_button("🔍 マッチング開始", use_container_width=True)

# メインエリア
if submit_button:
    # 候補者データを辞書形式に変換
    skills_list = [s.strip() for s in skills_input.split('\n') if s.strip()]
    desired_jobs_list = [j.strip() for j in desired_jobs_input.split('\n') if j.strip()]
    
    compromise_list = []
    if compromise_job:
        compromise_list.append("職種")
    if compromise_salary:
        compromise_list.append("年収")
    if compromise_location:
        compromise_list.append("勤務地")
    
    candidate = {
        "年齢": age,
        "現在の職種": current_job,
        "経験年数": years_exp,
        "スキル": skills_list,
        "希望業界": desired_industry,
        "希望職種": desired_jobs_list,
        "希望年収": desired_salary,
        "希望勤務地": desired_location,
        "妥協可能": compromise_list,
        "志向性": aspiration
    }
    
    # CSVファイル読み込み
    try:
        with st.spinner("求人データを読み込み中..."):
            jobs_df = pd.read_csv('jobs.csv')
            st.success(f"✅ {len(jobs_df)}件の求人データを読み込みました")
    except FileNotFoundError:
        st.error("❌ jobs.csvが見つかりません。ファイルをアップロードしてください。")
        st.stop()
    
    # マッチング実行
    with st.spinner("マッチング処理中..."):
        results = calculate_match_score(candidate, jobs_df)
    
    # フィルターUI
    st.header("🔧 フィルター設定")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_location = st.selectbox(
            "勤務地で絞り込み",
            ["すべて"] + list(jobs_df['勤務地'].unique()),
            index=0
        )
    
    with col2:
        filter_industry = st.text_input("業界キーワードで絞り込み", value="")
    
    with col3:
        min_score = st.slider("最低スコア", min_value=0, max_value=130, value=70, step=5)
    
    # フィルタリング実行
    filtered_results = filter_results(
        results,
        location_filter=None if filter_location == "すべて" else filter_location,
        industry_filter=filter_industry if filter_industry else None,
        min_score=min_score
    )
    
    # 統計情報表示
    st.header(f"📊 マッチング結果：{len(filtered_results)}件")
    
    if len(filtered_results) > 0:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("総求人数", len(jobs_df))
        col2.metric("該当求人数", len(filtered_results))
        col3.metric("最高スコア", f"{filtered_results[0]['総合スコア']:.1f}点")
        avg_score = sum(r['総合スコア'] for r in filtered_results[:10]) / min(10, len(filtered_results))
        col4.metric("平均スコア(上位10件)", f"{avg_score:.1f}点")
    
    # 結果表示
    st.header("🏆 おすすめ求人")
    
    # 表示件数選択
    display_count = st.selectbox("表示件数", [10, 20, 30, 50], index=0)
    
    if len(filtered_results) == 0:
        st.warning("⚠️ 該当する求人が見つかりませんでした。フィルター条件を緩和してください。")
    else:
        for i, result in enumerate(filtered_results[:display_count]):
            with st.container():
                st.markdown(f"### {i+1}位 - {result['企業名']}")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{result['タイトル']}**")
                    st.markdown(f"📍 {result['勤務地']} | 💰 {result['年収帯(低)']}〜{result['年収帯(高)']}万円")
                    st.markdown(f"🏷️ {result['ポジション']}")
                
                with col2:
                    st.markdown(f'<div class="score-badge">総合: {result["総合スコア"]:.1f}点</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="sub-score">受かる可能性: {result["受かる可能性"]:.1f}/80</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="sub-score">希望マッチ: {result["希望マッチ"]:.1f}/50</div>', unsafe_allow_html=True)
                
                # プログレスバー
                st.progress(result['総合スコア'] / 130)
                
                # 詳細情報（折りたたみ式）
                with st.expander("📋 求人詳細とマッチ理由"):
                    st.markdown("**求人概要**")
                    st.write(result['求人概要'])
                    
                    st.markdown("**必須要件**")
                    st.write(result['必須要件'])
                    
                    st.markdown("**マッチ理由**")
                    for reason in result['マッチ理由']:
                        st.markdown(f"- {reason}")
                
                st.markdown("---")
    
    # CSV出力ボタン
    if len(filtered_results) > 0:
        st.header("💾 結果のエクスポート")
        
        # DataFrameに変換
        export_df = pd.DataFrame(filtered_results)
        export_df = export_df[['企業名', 'タイトル', 'ポジション', '勤務地', '年収帯(低)', '年収帯(高)', '総合スコア', '受かる可能性', '希望マッチ']]
        
        csv = export_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 結果をCSVでダウンロード",
            data=csv,
            file_name=f"{name}_matching_results.csv",
            mime="text/csv"
        )

else:
    # 初期画面
    st.info("👈 左側のフォームに候補者情報を入力して、「マッチング開始」ボタンをクリックしてください。")
    
    st.markdown("""
    ## 📖 使い方
    
    1. **左側のサイドバー**に候補者情報を入力
       - 基本情報（名前・年齢）
       - 職務経歴（現在の職種・経験年数・スキル）
       - 希望条件（業界・職種・年収・勤務地）
       - 妥協可能なポイント
       - 志向性・キャリアビジョン
    
    2. **「マッチング開始」ボタン**をクリック
    
    3. **マッチング結果**が表示されます
       - 総合スコア順にランキング表示
       - フィルター機能で絞り込み可能
       - 詳細なマッチ理由を確認
       - 結果をCSVでエクスポート可能
    
    ---
    
    ### 📊 スコアリングの仕組み
    
    **総合スコア = 受かる可能性(80点) + 希望マッチ(50点) = 130点満点**
    
    #### 受かる可能性 (80点)
    - 職種マッチ: 最大35点
    - 経験年数マッチ: 最大20点
    - スキル・実績マッチ: 最大25点
    
    #### 希望マッチ (50点)
    - 業界マッチ: 最大20点
    - 年収マッチ: 最大10点
    - 勤務地マッチ: 最大10点
    - 志向性マッチ: 最大10点
    
    ※妥協可能な条件は点数が半減します
    """)
