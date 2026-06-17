import re
from collections import defaultdict
from datetime import datetime
import streamlit as st
import pandas as pd
from io import BytesIO

# 1. ตั้งค่าหน้าตาของโปรแกรมเบื้องต้น
st.set_page_config(page_title="Pim-Tang TH", page_icon="📝", layout="centered")

# 2. ใส่ Custom CSS เพื่อเปลี่ยนฟอนต์ทั้งแอปเป็น "Sarabun"
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"], stText, p, div, span, h1, h2, h3, h4, h5, h6, button, input, textarea {
        font-family: 'Sarabun', sans-serif !important;
    }
    /* ปรับฟอนต์สำหรับปุ่มกด (Streamlit Button) */
    .stButton button {
        font-family: 'Sarabun', sans-serif !important;
    }
    /* ปรับฟอนต์สำหรับช่องกรอกข้อมูล (Text Area) */
    .stTextArea textarea {
        font-family: 'Sarabun', sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# นิยามไอคอนเครื่องคิดเลข (เอาสไตล์ที่เป็นปีกกาออกเพื่อความปลอดภัย)
CALCULATOR_ICON = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="40" style="vertical-align: middle; margin-left: 10px;">
    <rect x="4" y="2" width="16" height="20" rx="3" fill="#2D2A4A"/>
    <rect x="6" y="4" width="12" height="4" rx="1" fill="#00D2C4"/>
    <line x1="8" y1="6" x2="14" y2="6" stroke="#2D2A4A" stroke-width="1.5" stroke-linecap="round"/>
    <circle cx="8" cy="11" r="1.2" fill="#F4F5F8"/>
    <circle cx="12" cy="11" r="1.2" fill="#F4F5F8"/>
    <circle cx="16" cy="11" r="1.2" fill="#FF6B6B"/>
    <circle cx="8" cy="15" r="1.2" fill="#F4F5F8"/>
    <circle cx="12" cy="15" r="1.2" fill="#F4F5F8"/>
    <circle cx="16" cy="15" r="1.2" fill="#FFD166"/>
    <circle cx="8" cy="19" r="1.2" fill="#F4F5F8"/>
    <rect x="10.8" y="17.8" width="6.4" height="2.4" rx="1.2" fill="#4B65F6"/>
</svg>
"""

# ใช้การเชื่อมสตริงด้วย + แทน f-string เพื่อป้องกันระบบเอ๋อ
st.markdown(
    '<h1 style="display: flex; align-items: center; white-space: nowrap;">Pim-Tang ' + CALCULATOR_ICON + '</h1>', 
    unsafe_allow_html=True
)

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

# ช่องสำหรับกรอกข้อมูลค่าใช้จ่าย (ใส่ตัวอย่างอเมซอน-สตาร์บัคส์กลับคืนมา)
data = st.text_area(
    "กรอกข้อมูลค่าใช้จ่ายของคุณ:",
    value="",
    height=200,
    placeholder="ตัวอย่างการกรอก:\n15 อเมซอน 60 สตาร์บัคส์ 160"
)

# ใส่คำอธิบายรูปแบบการกรอกใต้กล่องข้อความกลับมาตามเดิม
st.caption("💡 รูปแบบที่รองรับ: `[วันที่] [รายการ] [จำนวนเงิน] [รายการ] [จำนวนเงิน] ...` (เว้นวรรคแยกแต่ละส่วน)")

# ปุ่มกดคำนวณเงิน
if st.button("คำนวณเงิน", type="primary"):
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
            
            # ใช้ Regex ดึงคู่ [ชื่อรายการค่าใช้จ่าย] [จำนวนเงิน]
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
                st.subheader("🔖 วันธรรมดา (Weekday)")
                st.write(f"**รวมยอดเงินวันธรรมดา:** {round(total_weekday, 2)} บาท")

            with col2:
                st.subheader("🏷️ วันหยุด (Weekend)")
                st.write(f"**รวมยอดเงินวันหยุด:** {round(total_weekend, 2)} บาท")

            st.markdown("---")
            grand_total = total_weekday + total_weekend
            st.metric(label="💵 ยอดรวมทั้งหมด (Grand Total)", value=f"{round(grand_total, 2)} บาท")

            # แสดงตารางสรุปรายการทั้งหมด
            st.subheader("📋 รายการทั้งหมด")
            df = pd.DataFrame(all_rows)

            # 💡 เพิ่มบรรทัดนี้เพื่อเริ่ม Index ที่ 1
            df.index = df.index + 1 

            st.dataframe(df, use_container_width=True)

            # ส่วนการสร้างไฟล์ Excel สำหรับดาวน์โหลด
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="Expenses")

                # สร้างหน้าสรุปยอดรวมส่งออก Excel แบบง่ายๆ
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
