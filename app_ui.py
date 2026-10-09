from datetime import datetime
import requests
import streamlit as st

# عنوان الـ Backend اللي شغال
API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="نظام إدارة العيادة الطبية", page_icon="🏥", layout="wide"
)

st.title("🏥 نظام إدارة العيادة الطبية المحترف")
st.write(
    "لوحة تحكم متكاملة لإدارة المرضى والمواعيد بكل سهولة واحترافية."
)

# القائمة الجانبية للتنقل
menu = st.sidebar.selectbox(
    "اختر القسم",
    [
        "تسجيل مريض جديد",
        "بحث وعرض المرضى",
        "حجز موعد جديد",
        "عرض المواعيد",
    ],
)

# 1. تسجيل مريض جديد
if menu == "تسجيل مريض جديد":
  st.subheader("📝 تسجيل بيانات مريض جديد")
  with st.form("patient_form"):
    full_name = st.text_input("الاسم الكامل للمريض")
    phone = st.text_input("رقم الهاتف (فريد)")
    age = st.number_input("العمر", min_value=0, max_value=120, value=30)
    gender = st.selectbox("الجنس", ["ذكر", "أنثى"])
    medical_history = st.text_area("التاريخ المرضي / ملاحظات طبية")

    submit = st.form_submit_button("حفظ المريض")

    if submit:
      if full_name and phone:
        data = {
            "full_name": full_name,
            "phone": phone,
            "age": age,
            "gender": gender,
            "medical_history": medical_history,
        }
        response = requests.post(f"{API_URL}/patients/", json=data)
        if response.status_code == 200:
          st.success("تم تسجيل المريض بنجاح! 🚀")
        else:
          st.error(
              f"حدث خطأ: {response.json().get('detail', 'خطأ غير معروف')}"
          )
      else:
        st.warning("يرجى إدخال الاسم ورقم الهاتف على الأقل.")

# 2. بحث وعرض المرضى
elif menu == "بحث وعرض المرضى":
  st.subheader("🔍 البحث عن المرضى وعرضهم")
  search_query = st.text_input("ابحث بالاسم أو رقم الهاتف")

  url = f"{API_URL}/patients/"
  if search_query:
    url += f"?search={search_query}"

  response = requests.get(url)
  if response.status_code == 200:
    patients = response.json()
    if patients:
      for p in patients:
        with st.expander(
            f"👤 {p['full_name']} - الهاتف: {p['phone']}"
        ):
          st.write(f"**العمر:** {p['age']}")
          st.write(f"**الجنس:** {p['gender']}")
          st.write(f"**التاريخ المرضي:** {p['medical_history'] or 'لا يوجد'}")
          st.write(f"**تاريخ التسجيل:** {p['created_at']}")
    else:
      st.info("لا توجد نتائج مطابقة للبحث.")
  else:
    st.error("تعذر جلب بيانات المرضى.")

# 3. حجز موعد جديد
elif menu == "حجز موعد جديد":
  st.subheader("📅 حجز موعد جديد لمريض")
  # جلب قائمة المرضى أولاً لاختيار المريض
  res = requests.get(f"{API_URL}/patients/")
  if res.status_code == 200 and res.json():
    patients = res.json()
    patient_dict = {f"{p['full_name']} ({p['phone']})": p['id'] for p in patients}

    selected_patient_str = st.selectbox(
        "اختر المريض", list(patient_dict.keys())
    )
    patient_id = patient_dict[selected_patient_str]

    app_date = st.date_input("تاريخ المعد")
    app_time = st.time_input("وقت الموعد")
    reason = st.text_input("سبب الكشف / الشكوى")

    if st.button("تأكيد الحجز"):
      # دمج التاريخ والوقت
      combined_datetime = datetime.combine(app_date, app_time).isoformat()
      app_data = {
          "patient_id": patient_id,
          "appointment_date": combined_datetime,
          "reason": reason,
      }
      r = requests.post(f"{API_URL}/appointments/", json=app_data)
      if r.status_code == 200:
        st.success("تم حجز الموعد بنجاح! 🩺")
      else:
        st.error(
            f"فشل الحجز: {r.json().get('detail', 'تأكد من صحة البيانات')}"
        )
  else:
    st.warning("يجب تسجيل مريض واحد على الأقل قبل حجز الموعد.")

# 4. عرض المواعيد
elif menu == "عرض المواعيد":
  st.subheader("📋 جدول المواعيد المحجوزة")
  r = requests.get(f"{API_URL}/appointments/")
  if r.status_code == 200:
    appointments = r.json()
    if appointments:
      for appt in appointments:
        st.info(
            f"رقم الموعد: {appt['id']} | رقم المريض ID: {appt['patient_id']}"
            f" | التاريخ: {appt['appointment_date']} | السبب: {appt['reason']}"
            f" | الحالة: {appt['status']}"
        )
    else:
      st.info("لا توجد مواعيد مسجلة حتى الآن.")
  else:
    st.error("تعذر جلب المواعيد.")
