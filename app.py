from pathlib import Path

import joblib
import numpy as np
import streamlit as st

BASE = Path(__file__).parent

EXAMPLES = [
    'Uzcard: ваша карта 8600 **** 1234 заблокирована. Для разблокировки перейдите uzcard-verify.com',
    'Код подтверждения: 482913. Никому не сообщайте этот код',
    "Tabriklaymiz! Siz 500 000 so'm yutib oldingiz. Sovg'ani olish: prize-uzb.net",
    'Aziz, salom! Ertaga soat 9 da uchrashamizmi?',
]


@st.cache_resource
def load_model():
    return joblib.load(BASE / 'model.joblib')


def top_terms(model, text, k=6):
    """Words and fragments of the message that pushed the score towards 'fraud' the most."""
    features, clf = model.steps[0][1], model.steps[1][1]
    contrib = features.transform([text]).multiply(clf.coef_[0]).toarray()[0]
    names = features.get_feature_names_out()
    terms = []
    for i in np.argsort(contrib)[::-1]:
        if contrib[i] <= 0 or len(terms) == k:
            break
        term = names[i].split('__', 1)[1].strip()
        if len(term) >= 3 and not any(term in t or t in term for t in terms):
            terms.append(term)
    return terms


st.set_page_config(page_title='SMS Fraud UZ', layout='centered')
st.title('SMS Fraud UZ')
st.caption('Проверка SMS на мошенничество (узбекский и русский). Учебная модель на синтетических данных.')

model = load_model()
example = st.selectbox('Пример', [''] + EXAMPLES)
text = st.text_area('Текст SMS', value=example, height=120)

if st.button('Проверить', type='primary') and text.strip():
    p = model.predict_proba([text])[0, 1]
    if p >= 0.5:
        st.error(f'Похоже на мошенничество: {p:.0%}')
        hints = top_terms(model, text)
        if hints:
            st.write('Подозрительные фрагменты:', ', '.join(f'`{h}`' for h in hints))
    else:
        st.success(f'Похоже на обычное сообщение. Вероятность мошенничества: {p:.0%}')
