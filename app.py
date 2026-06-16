import re
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
from io import BytesIO

# 1. ตั้งค่าหน้าตาของโปรแกรมเบื้องต้น
st.set_page_config(page_title="Expense Tracker TH", page_icon="💰", layout="centered")

# 2. ใส่ Custom CSS เพื่อเปลี่ยนฟอนต์ทั้งแอปเป็น "Prompt"
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"], stText, p, div, span, h1, h2, h3, h4, h5, h6, button, input, textarea {
        font-family: 'Prompt', sans-serif !important;
    }
    /* ปรับฟอนต์สำหรับปุ่มกด (Streamlit Button) */
    .stButton button {
        font-family: 'Prompt', sans-serif !important;
    }
    /* ปรับฟอนต์สำหรับช่องกรอกข้อมูล (Text Area) */
    .stTextArea textarea {
        font-family: 'Prompt', sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# หัวข้อหลัก
st.title("Expense Tracker TH 🇹🇭")

YEAR = 2026

# รายชื่อเดือนภาษาไทยสั้น
TH_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]

def is_weekend(day_num):
    """ตรวจสอบว่าเป็นวันเสาร์-อาทิตย์ไหม โดยอิงจากวัน, เดือนปัจจุบัน และปี 2026"""
    now = datetime.now()
    current_month = now.month
    current_year = YEAR
    
    try:
        dt = datetime(current_year, current_month, int(day_num))
        return dt.weekday() >= 5, dt.strftime(f"%d/%m/{current_year}")
    except ValueError:
        return False, f"{day_num} (วันที่ไม่ถูกต้อง)"

# หมวดหมู่สำหรับจัดกลุ่มค่าใช้จ่าย
CATEGORY_EMOJI = {
    "food": "🥩",
    "drink": "🥤",
    "misc": "📦",
}

def analyze_category(item_name):
    """ฟังก์ชันช่วยเดาหมวดหมู่จากชื่อรายการแบบง่ายๆ จากคำหลัก"""
    item_name = item_name.lower()
    if any(keyword in item_name for keyword in ["ข้าว", "ก๋วยเตี๋ยว", "อาหาร", "หมูกระทะ", "ส้มตำ", "ชาบู"]):
        return "food"
    elif any(keyword in item_name for keyword in ["กาแฟ", "ชา", "น้ำ", "นม", "ชาเขียว", "ชาเย็น", "coffee"]):
        return "drink"
    return "misc"

# ช่องสำหรับกรอกข้อมูลค่าใช้จ่าย
data = st.text_area(
    "กรอกข้อมูลค่าใช้จ่ายของคุณ:",
    value="",
    height=200,
    placeholder="ตัวอย่างการกรอก:\n15 กาแฟ 15 ชาเขียว 15\n16 ชาเย็น 45 ข้าวผัด 50"
)

st.caption("💡 รูปแบบที่รองรับ: `[วันที่] [รายการ] [จำนวนเงิน] [รายการ] [จำนวนเงิน] ...` (เว้นวรรคแยกแต่ละส่วน)")

# ปุ่มกดคำนวณเงิน
if st.button("คำนวณเงิน", type="primary"):
    if not data.strip():
        st.warning("โปรดกรอกข้อมูลก่อนคำนวณ")
    else:
        totals_weekday = defaultdict(float)
        totals_weekend = defaultdict(float)
        all_rows = []

        for line in data.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            day_part = parts[0]
            
            if not day_part.isdigit():
                st.error(f"⚠️ บรรทัดนี้ไม่ได้ขึ้นต้นด้วยวันที่ที่ถูกต้อง: '{line}'")
                continue
                
            weekend, formatted_date = is_weekend(day_part)
            day_type = "Weekend" if weekend else "Weekday"
            items_part = " ".join(parts[1:])
            
            # ใช้ Regex ดึงคู่ [ชื่อรายการค่าใช้จ่าย] [จำนวนเงิน] รองรับการพิมพ์ต่อกันในหนึ่งวัน
            items = re.findall(r'([^\d\s]+)\s+(\d+(?:\.\d+)?)', items_part)
            
            if not items:
                st.warning(f"🔎 ไม่พบรายการค่าใช้จ่ายในวันที่ {day_part}: '{items_part}'")
                continue

            for item, amount in items:
                amount = float(amount)
                category = analyze_category(item)

                if weekend:
                    totals_weekend[category] += amount
                else:
                    totals_weekday[category] += amount

                all_rows.append({
                    "Date": formatted_date,
                    "Item": item,
                    "Category": category,
                    "Amount": amount,
                    "Type": day_type
                })

        # แสดงผลลัพธ์เมื่อมีข้อมูลที่ประมวลผลได้
        if all_rows:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 วันธรรมดา (Weekday)")
                total_wd = 0
                for category in CATEGORY_EMOJI:
                    amt = totals_weekday.get(category, 0)
                    if amt:
                        st.write(f"{CATEGORY_EMOJI[category]} **{category.capitalize()}**: {round(amt, 2)} บาท")
                        total_wd += amt
                st.write(f"**รวมวันธรรมดา:** {round(total_wd, 2)} บาท")

            with col2:
                st.subheader("🏖️ วันหยุด (Weekend)")
                total_we = 0
                for category in CATEGORY_EMOJI:
                    amt = totals_weekend.get(category, 0)
                    if amt:
                        st.write(f"{CATEGORY_EMOJI[category]} **{category.capitalize()}**: {round(amt, 2)} บาท")
                        total_we += amt
                st.write(f"**รวมวันหยุด:** {round(total_we, 2)} บาท")

            st.markdown("---")
            grand_total = sum(totals_weekday.values()) + sum(totals_weekend.values())
            st.metric(label="💰 ยอดรวมทั้งหมด (Grand Total)", value=f"{round(grand_total, 2)} บาท")

            # แสดงตารางสรุปรายการ
            st.subheader("📋 รายการทั้งหมด")
            df = pd.DataFrame(all_rows)
            st.dataframe(df, use_container_width=True)

            # ส่วนการสร้างไฟล์ Excel สำหรับดาวน์โหลด
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Expenses")

                summary_data = []
                for cat in CATEGORY_EMOJI:
                    summary_data.append({
                        "Category": cat,
                        "Weekday Total": totals_weekday.get(cat, 0),
                        "Weekend Total": totals_weekend.get(cat, 0),
                    })
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, index=False, sheet_name="Summary")

            output.seek(0)

            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ Excel (.xlsx)",
                data=output,
                file_name=f"expenses_report_{YEAR}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
