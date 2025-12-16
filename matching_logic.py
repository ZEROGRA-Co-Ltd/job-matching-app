"""
求人マッチングロジック
候補者情報と求人データベースをマッチングし、スコアリングを行う
"""
import pandas as pd
import re


def calculate_match_score(candidate, jobs_df):
    """
    候補者情報と求人データをマッチングし、スコアリングを実行
    
    Args:
        candidate (dict): 候補者情報
        jobs_df (pd.DataFrame): 求人データベース
    
    Returns:
        list: マッチング結果のリスト（スコア降順）
    """
    results = []
    
    for index, job in jobs_df.iterrows():
        total_score = 0
        likelihood_score = 0  # 受かる可能性 (80点満点)
        preference_score = 0  # 希望条件マッチ (50点満点)
        match_reasons = []
        
        # ==========================================
        # 受かる可能性スコア (80点満点)
        # ==========================================
        
        # --- 職種マッチ (35点満点) ---
        job_match_points = 0
        job_match_reason = ""
        
        candidate_current_job_lower = str(candidate.get("現在の職種", "")).lower()
        candidate_desired_jobs = candidate.get("希望職種", [])
        if isinstance(candidate_desired_jobs, str):
            candidate_desired_jobs = [candidate_desired_jobs]
        
        job_position_lower = str(job["ポジション（職種）"]).lower()
        
        # 希望職種との完全一致チェック
        for desired_job in candidate_desired_jobs:
            desired_job_lower = str(desired_job).lower()
            if desired_job_lower == job_position_lower:
                job_match_points = 35
                job_match_reason = f"希望職種 '{desired_job}' が募集職種と完全に一致しました。"
                break
            elif desired_job_lower in job_position_lower or job_position_lower in desired_job_lower:
                job_match_points = max(job_match_points, 25)
                job_match_reason = f"希望職種 '{desired_job}' が募集職種 '{job['ポジション（職種）']}' に関連します。"
        
        # 現在の職種との一致チェック（希望職種より低い点数）
        if job_match_points == 0:
            if candidate_current_job_lower == job_position_lower:
                job_match_points = 20
                job_match_reason = f"現在の職種 '{candidate['現在の職種']}' が募集職種と一致しました。"
            elif candidate_current_job_lower in job_position_lower or job_position_lower in candidate_current_job_lower:
                job_match_points = 15
                job_match_reason = f"現在の職種 '{candidate['現在の職種']}' が募集職種に関連します。"
        
        if job_match_points == 0:
            job_match_reason = f"職種がマッチしませんでした (希望: {', '.join(candidate_desired_jobs)}, 現在: {candidate['現在の職種']} vs 募集: {job['ポジション（職種）']})。"
        
        likelihood_score += job_match_points
        match_reasons.append(f"職種マッチ: {job_match_points}点 ({job_match_reason})")
        
        # --- 経験年数マッチ (20点満点) ---
        experience_match_points = 0
        required_experience_years = 0
        experience_reason = ""
        job_must_have_lower = str(job['必須要件']).lower()
        
        experience_match = re.search(r'(\d+)年以上', job_must_have_lower)
        if experience_match:
            required_experience_years = int(experience_match.group(1))
            if candidate['経験年数'] >= required_experience_years:
                experience_match_points = 20
                experience_reason = f"必須経験年数({required_experience_years}年以上)を満たしています (候補者経験: {candidate['経験年数']}年)。"
            else:
                experience_reason = f"必須経験年数({required_experience_years}年以上)を満たしていません (候補者経験: {candidate['経験年数']}年)。"
        elif pd.isna(job['必須要件']) or not job_must_have_lower.strip():
            experience_match_points = 20
            experience_reason = "必須要件に経験年数の記載がありません（適合と判断）。"
        else:
            experience_match_points = 20
            experience_reason = "必須要件に特定の経験年数の記載がありません（適合と判断）。"
        
        likelihood_score += experience_match_points
        match_reasons.append(f"経験年数マッチ: {experience_match_points}点 ({experience_reason})")
        
        # --- スキル・実績マッチ (25点満点) ---
        skill_match_points = 0
        matched_skills_count = 0
        matched_skills_list = []
        
        candidate_skills = candidate.get('スキル', [])
        if isinstance(candidate_skills, str):
            candidate_skills = [candidate_skills]
        
        if candidate_skills:
            job_required_skills_text = str(job['必須要件']).lower()
            
            for skill in candidate_skills:
                if str(skill).lower() in job_required_skills_text:
                    matched_skills_count += 1
                    matched_skills_list.append(skill)
            
            skill_match_points = (matched_skills_count / len(candidate_skills)) * 25
        
        skill_match_reason = f"{matched_skills_count}/{len(candidate_skills)}個のスキルがマッチしました。"
        if matched_skills_list:
            skill_match_reason += f" (マッチスキル: {', '.join(matched_skills_list)})"
        
        likelihood_score += skill_match_points
        match_reasons.append(f"スキルマッチ: {round(skill_match_points, 1)}点 ({skill_match_reason})")
        
        # ==========================================
        # 希望条件マッチスコア (50点満点)
        # ==========================================
        
        # --- 業界マッチ (20点満点) ---
        industry_match_points = 0
        industry_reason = ""
        
        desired_industry = candidate.get("希望業界", "")
        job_summary = str(job.get('求人概要', '')).lower()
        job_title = str(job.get('タイトル', '')).lower()
        job_company = str(job.get('企業名', '')).lower()
        
        if desired_industry:
            desired_industry_lower = desired_industry.lower()
            
            # 企業名、求人タイトル、求人概要に業界キーワードが含まれるかチェック
            if (desired_industry_lower in job_company or 
                desired_industry_lower in job_title or 
                desired_industry_lower in job_summary):
                industry_match_points = 20
                industry_reason = f"希望業界 '{desired_industry}' に該当する求人です。"
            else:
                industry_reason = f"希望業界 '{desired_industry}' との明確な関連が見つかりませんでした。"
        else:
            industry_match_points = 20
            industry_reason = "業界指定なし（適合と判断）。"
        
        preference_score += industry_match_points
        match_reasons.append(f"業界マッチ: {industry_match_points}点 ({industry_reason})")
        
        # --- 年収マッチ (10点満点) ---
        salary_match_points = 0
        salary_reason = ""
        desired_salary = candidate.get('希望年収', 0)
        
        if job['年収帯(低)'] <= desired_salary <= job['年収帯(高)']:
            salary_match_points = 10
            salary_reason = f"希望年収({desired_salary}万円)が求人の年収帯({job['年収帯(低)']}-{job['年収帯(高)']}万円)に収まっています。"
        elif desired_salary < job['年収帯(低)']:
            salary_match_points = 10
            salary_reason = f"希望年収({desired_salary}万円)を上回る年収帯({job['年収帯(低)']}-{job['年収帯(高)']}万円)です。"
        else:
            salary_reason = f"希望年収({desired_salary}万円)が求人の年収帯({job['年収帯(低)']}-{job['年収帯(高)']}万円)を上回っています。"
        
        # 妥協条件の処理
        compromise_list = candidate.get('妥協可能', [])
        if isinstance(compromise_list, str):
            compromise_list = [compromise_list]
        
        if "年収" in compromise_list:
            salary_match_points /= 2
            salary_reason += " (年収は妥協可能な条件のため、点数半減)"
        
        preference_score += salary_match_points
        match_reasons.append(f"年収マッチ: {round(salary_match_points, 1)}点 ({salary_reason})")
        
        # --- 勤務地マッチ (10点満点) ---
        location_match_points = 0
        location_reason = ""
        desired_location = candidate.get('希望勤務地', '')
        job_location = str(job['勤務地'])
        
        # 勤務地が複数ある場合の処理
        if isinstance(job_location, str) and '、' in job_location:
            job_locations = [loc.strip() for loc in job_location.split('、')]
        else:
            job_locations = [job_location]
        
        if desired_location in job_locations:
            location_match_points = 10
            location_reason = f"希望勤務地('{desired_location}')が求人の勤務地と一致します。"
        elif any(desired_location in loc or loc in desired_location for loc in job_locations):
            location_match_points = 10
            location_reason = f"希望勤務地('{desired_location}')が求人の勤務地('{job_location}')に含まれます。"
        else:
            location_reason = f"希望勤務地('{desired_location}')が求人の勤務地('{job_location}')と一致しません。"
        
        # 妥協条件の処理
        if "勤務地" in compromise_list:
            location_match_points /= 2
            location_reason += " (勤務地は妥協可能な条件のため、点数半減)"
        
        preference_score += location_match_points
        match_reasons.append(f"勤務地マッチ: {round(location_match_points, 1)}点 ({location_reason})")
        
        # --- 志向性マッチ (10点満点) ---
        aspiration_match_points = 0
        aspiration_reason = ""
        
        aspiration = candidate.get("志向性", "")
        if aspiration:
            aspiration_lower = aspiration.lower()
            job_summary_lower = str(job.get('求人概要', '')).lower()
            job_title_lower = str(job.get('タイトル', '')).lower()
            
            # 志向性キーワードを求人概要・タイトルから検索
            aspiration_keywords = []
            if "組織" in aspiration_lower or "マネジメント" in aspiration_lower:
                aspiration_keywords.extend(["組織", "マネジメント", "mgr", "マネージャー", "リーダー", "育成"])
            if "採用" in aspiration_lower:
                aspiration_keywords.extend(["採用", "人事", "hr", "リクルート"])
            if "企画" in aspiration_lower or "戦略" in aspiration_lower:
                aspiration_keywords.extend(["企画", "戦略", "立案", "事業開発"])
            
            matched_aspiration_keywords = []
            for keyword in aspiration_keywords:
                if keyword in job_summary_lower or keyword in job_title_lower:
                    matched_aspiration_keywords.append(keyword)
            
            if matched_aspiration_keywords:
                aspiration_match_points = min(10, len(matched_aspiration_keywords) * 3)
                aspiration_reason = f"志向性に合致するキーワード ({', '.join(matched_aspiration_keywords)}) が見つかりました。"
            else:
                aspiration_reason = "志向性との明確な関連が見つかりませんでした。"
        else:
            aspiration_match_points = 10
            aspiration_reason = "志向性の指定なし（適合と判断）。"
        
        preference_score += aspiration_match_points
        match_reasons.append(f"志向性マッチ: {aspiration_match_points}点 ({aspiration_reason})")
        
        # 総合スコアを計算
        total_score = likelihood_score + preference_score
        
        results.append({
            '企業名': job['企業名'],
            'タイトル': job['タイトル'],
            'ポジション': job['ポジション（職種）'],
            '勤務地': job['勤務地'],
            '年収帯(低)': job['年収帯(低)'],
            '年収帯(高)': job['年収帯(高)'],
            '求人概要': job['求人概要'],
            '必須要件': job['必須要件'],
            '総合スコア': total_score,
            '受かる可能性': likelihood_score,
            '希望マッチ': preference_score,
            'マッチ理由': match_reasons
        })
    
    # スコアの高い順にソート
    results.sort(key=lambda x: x['総合スコア'], reverse=True)
    
    return results


def filter_results(results, location_filter=None, industry_filter=None, min_score=0):
    """
    マッチング結果をフィルタリング
    
    Args:
        results (list): マッチング結果
        location_filter (str): 勤務地フィルター
        industry_filter (str): 業界フィルター（企業名で検索）
        min_score (float): 最低スコア
    
    Returns:
        list: フィルタリングされた結果
    """
    filtered = results
    
    if location_filter:
        filtered = [r for r in filtered if location_filter in str(r['勤務地'])]
    
    if industry_filter:
        filtered = [r for r in filtered 
                   if industry_filter.lower() in str(r['企業名']).lower() or
                      industry_filter.lower() in str(r['タイトル']).lower() or
                      industry_filter.lower() in str(r['求人概要']).lower()]
    
    if min_score > 0:
        filtered = [r for r in filtered if r['総合スコア'] >= min_score]
    
    return filtered
