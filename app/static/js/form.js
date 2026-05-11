// 클라이언트 폼 검증 보강.
// 서버 측 Pydantic 검증이 최종이지만, UX 향상을 위해 사전 검증.

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('survey-form');
    if (!form) return;

    const submitBtn = document.getElementById('submit-btn');

    // ─────────────────────────────────────────────
    // 기타 라디오 ↔ 텍스트 입력 연동
    // 텍스트 입력 시 기타 라디오 자동 선택
    // ─────────────────────────────────────────────
    const otherRadio = document.getElementById('tech_cat_other_radio');
    const otherTxt = document.getElementById('tech_cat_other_text');
    if (otherRadio && otherTxt) {
        otherTxt.addEventListener('input', () => {
            if (otherTxt.value.trim() !== '') otherRadio.checked = true;
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

        // 기술분류 라디오: 정확히 1개 선택 필수
        // (HTML required 속성이 처리하지만 사용자 친화적 메시지를 위해 한 번 더)
        const techCatSelected = form.querySelector('input[name="tech_category"]:checked');
        if (!techCatSelected) {
            errors.push('기술 분류 1개를 선택해 주십시오.');
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

        // 기타 선택 시 텍스트 필수
        if (otherRadio?.checked && !otherTxt?.value.trim()) {
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
