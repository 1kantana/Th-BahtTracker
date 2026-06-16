import re
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
from io import BytesIO

# 1. ตั้งค่าหน้าตาของโปรแกรมเบื้องต้น
st.set_page_config(page_title="Pim-Tang TH", page_icon="💸", layout="centered")

# 2. ใส่ Custom CSS เพื่อเปลี่ยนฟอนต์ทั้งแอปเป็น "Sarabun"
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"], stText, p, div, span, h1, h2, h3, h4, h5, h6, button, input, textarea {
        font-family: 'Sarabun', sans-serif !important;
    }
    .stButton button {
        font-family: 'Sarabun', sans-serif !important;
    }
    .stTextArea textarea {
        font-family: 'Sarabun', sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# หัวข้อหลักบนหน้าเว็บ
st.title("Pim-Tang TH 🇹🇭")

YEAR = 2026

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

# ช่องสำหรับกรอกข้อมูลค่าใช้จ่าย
data = st.text_area(
    "กรอกข้อมูลค่าใช้จ่ายของคุณ:",
    value="",
    height=200,
)

# ปุ่มกดคำนวณเงิน
is_calculated = st.button("คำนวณเงิน", type="primary")

# --- ส่วนแนะนำการกรอกข้อมูลด้านล่าง (แสดงเมื่อหน้าจอโล่ง / ยังไม่ได้กดคำนวณ) ---
if not is_calculated:
    st.markdown("---")
    st.markdown("### 💡 แนะนำวิธีการกรอกข้อมูล")
    
    # ใช้ st.info เพื่อแสดงรูปแบบที่ถูกต้องอย่างชัดเจน
    st.info(
        "**รูปแบบการกรอก:** พิมพ์ขึ้นต้นด้วย `[วันที่]` ตามด้วย `[ชื่อรายการ]` และ `[จำนวนเงิน]` สลับกันไปในบรรทัดเดียวกัน (เว้นวรรค 1 เคาะระหว่างส่วน)\n\n"
        "**ตัวอย่างเช่น:**\n"
        "`15 กาแฟ 60 ข้าวผัด 50` (แปลว่า วันที่ 15 ซื้อกาแฟ 60 บาท และข้าวผัด 50 บาท)\n"
        "`16 ชาเย็น 45` (แปลว่า วันที่ 16 ซื้อชาเย็น 45 บาท)"
    )
    
    # ใช้ Expander ซ่อนรายละเอียดข้อกำหนดไว้ เพื่อไม่ให้หน้าจอดูกลืนหรือรกเกินไป
    with st.expander("🔍 ดูรายละเอียดข้อกำหนดเพิ่มเติม"):
        st.markdown(
            """
            * **วันที่:** ให้ใส่เฉพาะ *ตัวเลขวันที่* (เช่น 1 ถึง 31) ของเดือนปัจจุบันเท่านั้น ระบบจะคำนวณประเภทวันให้โดยอัตโนมัติ
            * **การขึ้นบรรทัดใหม่:** 1 บรรทัด = 1 วัน คุณสามารถใส่กี่รายการในบรรทัดนั้นก็ได้
            * **รายการและจำนวนเงิน:** ต้องอยู่คู่กันเสมอ โดยตัวชื่อรายการต้อง *ไม่มีตัวเลขผสม* และจำนวนเงินต้อง *ไม่มีตัวอักษรผสม*
            * **ตัวอย่างการกรอกหลายวันพร้อมกัน:**
```text
              15 กาแฟ 60 ข้าวกลางวัน 80
              16 ค่ารถ 40 ชาเขียว 55 ขนม 20
              ```
            """
        )

# ประมวลผลเมื่อปุ่มถูกกด
if is_calculated:
    if not data.strip():
        st.warning("โปรดกรอกข้อมูลก่อนคำนวณ")
    else:
        total_weekday = 0.0
        total_weekend = 0.0
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
            
            items = re.findall(r'([^\d\s]+)\s+(\d+(?:\.\d+)?)', items_part)
            
            if not items:
                st.warning(f"🔎 ไม่พบรายการค่าใช้จ่ายในวันที่ {day_part}: '{items_part}'")
                continue

            for item, amount in items:
                amount = float(amount)

                if weekend:
                    total_weekend += amount
                else:
                    total_weekday += amount

                all_rows.append({
                    "Date": formatted_date,
                    "Item": item,
                    "Amount": amount,
                    "Type": day_type
                })

        # แสดงผลลัพธ์เมื่อประมวลผลเสร็จ
        if all_rows:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 วันธรรมดา (Weekday)")
                st.write(f"**รวมยอดเงินวันธรรมดา:** {round(total_weekday, 2)} บาท")

            with col2:
                st.subheader("🌞 วันหยุด (Weekend)")
                st.write(f"**รวมยอดเงินวันหยุด:** {round(total_weekend, 2)} บาท")

            st.markdown("---")
            grand_total = total_weekday + total_weekend
            st.metric(label="💳 ยอดรวมทั้งหมด (Grand Total)", value=f"{round(grand_total, 2)} บาท")

            st.subheader("📋 รายการทั้งหมด")
            df = pd.DataFrame(all_rows)
            st.dataframe(df, use_container_width=True)

            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Expenses")

                summary_data = [
                    {"Type": "Weekday Total", "Amount": total_weekday},
                    {"Type": "Weekend Total", "Amount": total_weekend},
                    {"Type": "Grand Total", "Amount": grand_total}
                ]
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, index=False, sheet_name="Summary")

            output.seek(0)

            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ Excel (.xlsx)",
                data=output,
                file_name=f"pim_tang_report_{YEAR}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
