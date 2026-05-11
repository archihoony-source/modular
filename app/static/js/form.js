// 클라이언트 폼 검증 보강.
// 서버 측 Pydantic 검증이 최종이지만, UX 향상을 위해 사전 검증.

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('survey-form');
    if (!form) return;

    const submitBtn = document.getElementById('submit-btn');

    // ─────────────────────────────────────────────
    // 기타 체크박스 ↔ 텍스트 입력 연동
    // ─────────────────────────────────────────────
    const otherChk = document.getElementById('tech_cat_other');
    const otherTxt = document.getElementById('tech_cat_other_text');
    if (otherChk && otherTxt) {
        otherTxt.addEventListener('input', () => {
            if (otherTxt.value.trim() !== '') otherChk.checked = true;
        });
    }

    // ─────────────────────────────────────────────
    // 키워드 카운터 (10개 초과 경고)
    // ─────────────────────────────────────────────
    const kwInput = document.getElementById('keywords');
    if (kwInput) {
        kwInput.addEventListener('input', () => {
            const parts = kwInput.value.split(',').map(s => s.trim()).filter(Boolean);
            kwInput.style.borderColor = parts.length > 10 ? '#dc2626' : '';
        });
    }

    // ─────────────────────────────────────────────
    // 폼 제출 전 검증
    // ─────────────────────────────────────────────
    form.addEventListener('submit', (e) => {
        const errors = [];

        // 기술분류 최소 1개
        const techCats = [
            'tech_cat_rc_competitive', 'tech_cat_zero_fatality',
            'tech_cat_marketability', 'tech_cat_scaleup', 'tech_cat_other',
        ];
        const techCatChecked = techCats.some(n => form.querySelector(`input[name="${n}"]`)?.checked);
        if (!techCatChecked) {
            errors.push('기술 분류를 1개 이상 선택해 주십시오.');
        }

        // 성과물 유형 최소 1개
        const outputTypes = [
            'output_type_system', 'output_type_method', 'output_type_material',
            'output_type_software', 'output_type_equipment', 'output_type_standard',
        ];
        const outChecked = outputTypes.some(n => form.querySelector(`input[name="${n}"]`)?.checked);
        if (!outChecked) {
            errors.push('성과물 유형을 1개 이상 선택해 주십시오.');
        }

        // 기타 체크 시 텍스트 필수
        if (otherChk?.checked && !otherTxt?.value.trim()) {
            errors.push('"기타" 선택 시 내용을 입력해 주십시오.');
        }

        if (errors.length > 0) {
            e.preventDefault();
            alert(errors.join('\n'));
            return;
        }

        // 제출 중 더블클릭 방지
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = '제출 중...';
        }
    });
});
