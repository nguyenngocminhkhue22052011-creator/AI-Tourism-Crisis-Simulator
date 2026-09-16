# 1. Import libraries

import tkinter as tk
import json
import random
import re
from google import genai
client = genai.Client()
weights = {
    "decision_making": 0.25,
    "risk_management": 0.20,
    "customer_service": 0.20,
    "financial_management": 0.15,
    "reputation_management": 0.10,
    "feasibility": 0.10
}
# 2. Game state
state = {
    "round": 1,
    "satisfaction": 50,
    "reputation": 50,
    "history": []
}

with open("crises.json", "r", encoding="utf-8") as f:
    crises = json.load(f)
used_crises = set()
crisis = None
answered = False
def format_money(amount):
    return f"{amount / 1000000000:.2f} tỷ VNĐ"

# 3. AI helper functions
def ask_ai(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
        print("AI RESPONSE:")
        print(response.text)
        return response.text
    except Exception as e:
        print("AI error:", e)
        return None

def get_json(text):
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            print("AI không trả về JSON:", text)
            return None
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            print("JSON AI trả về không hợp lệ:", text)
            return None

# 4. Create crisis
def create_crisis():
    available = [c for c in crises if c["id"] not in used_crises]
    if not available:
        used_crises.clear()
        available = crises
    crisis = random.choice(available)
    used_crises.add(crisis["id"])
    return crisis

# 5. Evaluate decision
def evaluate_decision(decision, reasoning):
    prompt = f"""
Bạn là chuyên gia quản lý khủng hoảng du lịch.
Hãy đánh giá quyết định của người chơi dựa trên tình huống cụ thể dưới đây.

TÌNH HUỐNG:
{json.dumps(crisis, ensure_ascii=False)}

QUYẾT ĐỊNH CỦA NGƯỜI CHƠI:
{decision}

GIẢI THÍCH CỦA NGƯỜI CHƠI:
{reasoning}

Hãy chấm điểm từ 0 đến 10 cho 6 tiêu chí:
- decision_making
- risk_management
- customer_service
- financial_management
- reputation_management
- feasibility

Hãy nhận xét CỤ THỂ dựa trên chính tình huống và quyết định của người chơi.

Cần trả về:
- strengths: điểm mạnh cụ thể
- weaknesses: điểm hạn chế cụ thể
- feedback: lời khuyên cụ thể
- budget_change: thay đổi ngân sách
- satisfaction_change: thay đổi mức hài lòng của khách
- reputation_change: thay đổi danh tiếng

satisfaction_change phải nằm trong khoảng -15 đến 15.
reputation_change phải nằm trong khoảng -15 đến 15.

budget_change là số tiền thay đổi trong ngân sách GAME.
Ngân sách ban đầu của game là 10000.
Không sử dụng tiền thật hoặc đơn vị tiền thực tế lớn như hàng triệu, tỷ.
budget_change phải nằm trong khoảng -5000 đến 1000.
Với một hành động có chi phí lớn, hãy ước tính chi phí trong phạm vi ngân sách của game.

CHỈ TRẢ VỀ JSON HỢP LỆ.
KHÔNG viết markdown.
KHÔNG viết ```json.
KHÔNG giải thích bên ngoài JSON.

JSON phải có đúng dạng:

{{
    "decision_making": 0,
    "risk_management": 0,
    "customer_service": 0,
    "financial_management": 0,
    "reputation_management": 0,
    "feasibility": 0,
    "strengths": "Nhận xét cụ thể",
    "weaknesses": "Nhận xét cụ thể",
    "feedback": "Lời khuyên cụ thể",
    "satisfaction_change": 0,
    "reputation_change": 0
}}
"""
    result = ask_ai(prompt)
    data = get_json(result)

    if not data:
        print("AI không trả về JSON hợp lệ. Đang dùng dữ liệu mặc định.")
        data = {
            "decision_making": 6,
            "risk_management": 6,
            "customer_service": 6,
            "financial_management": 6,
            "reputation_management": 6,
            "feasibility": 6,
            "strengths": "Không thể đọc kết quả đánh giá từ AI.",
            "weaknesses": "AI không trả về dữ liệu đúng định dạng.",
            "feedback": "Kiểm tra phản hồi của AI trong Terminal.",
            "budget_change": 0,
            "satisfaction_change": 0,
            "reputation_change": 0
        }

    total = 0

    for key in weights:
        try:
            data[key] = float(data.get(key, 5))
        except:
            data[key] = 5

        data[key] = max(0, min(10, data[key]))
        total += data[key] * weights[key]

    data["total"] = round(total * 10, 1)

    try:
        data["budget_change"] = max(-5000000000, min(2000000000, data["budget_change"]))
    except:
        data["budget_change"] = 0

    try:
        data["satisfaction_change"] = float(data.get("satisfaction_change", 0))
    except:
        data["satisfaction_change"] = 0

    try:
        data["reputation_change"] = float(data.get("reputation_change", 0))
    except:
        data["reputation_change"] = 0

    data["satisfaction_change"] = max(-15, min(15, data["satisfaction_change"]))
    data["reputation_change"] = max(-15, min(15, data["reputation_change"]))

    return data

# 6. Game logic
def update_status():
    status.config(
        text=f"Vòng {state['round']}/5 | Hài lòng: {state['satisfaction']:.0f}/100 | Danh tiếng: {state['reputation']:.0f}/100"
    )

def show_crisis():
    global crisis, answered
    crisis = create_crisis()
    answered = False
    crisis_text.delete("1.0", tk.END)
    decision_entry.delete(0, tk.END)
    reason_text.delete("1.0", tk.END)
    result_text.delete("1.0", tk.END)
    crisis_text.insert(
        tk.END,
        f"{crisis['title']}\n\n"
        f"Loại: {crisis['type']}\n"
        f"Mức độ: {crisis['severity']}/10\n"
        f"Số khách bị ảnh hưởng: {crisis['affected_tourists']}\n\n"
        f"{crisis['description']}"
    )
    evaluate_button.config(state="normal")
    next_button.config(state="disabled")
    update_status()

def evaluate():
    global answered
    if answered:
        return
    decision = decision_entry.get().strip()
    reasoning = reason_text.get("1.0", tk.END).strip()
    if not decision or not reasoning:
        result_text.delete("1.0", tk.END)
        result_text.insert(tk.END, "Vui lòng nhập quyết định và lý do.")
        return
    result = evaluate_decision(decision, reasoning)
    state["satisfaction"] += result["satisfaction_change"]
    state["reputation"] += result["reputation_change"]
    state["satisfaction"] = max(0, min(100, state["satisfaction"]))
    state["reputation"] = max(0, min(100, state["reputation"]))
    state["history"].append({
        "round": state["round"],
        "crisis": crisis["title"],
        "decision": decision,
        "reasoning": reasoning,
        "score": result["total"]
    })
    result_text.delete("1.0", tk.END)
    result_text.insert(
        tk.END,
        f"ĐIỂM TỔNG: {result['total']}/100\n\n"
        f"Ra quyết định: {result['decision_making']:.1f}/10\n"
        f"Quản lý rủi ro: {result['risk_management']:.1f}/10\n"
        f"Chăm sóc khách hàng: {result['customer_service']:.1f}/10\n"
        f"Quản lý tài chính: {result['financial_management']:.1f}/10\n"
        f"Quản lý danh tiếng: {result['reputation_management']:.1f}/10\n"
        f"Tính khả thi: {result['feasibility']:.1f}/10\n\n"
        f"Ưu điểm:\n{result['strengths']}\n\n"
        f"Điểm hạn chế:\n{result['weaknesses']}\n\n"
        f"Nhận xét:\n{result['feedback']}\n\n"
        f"Mức hài lòng: {result['satisfaction_change']:+.0f}\n"
        f"Danh tiếng: {result['reputation_change']:+.0f}"
    )
    answered = True
    evaluate_button.config(state="disabled")
    next_button.config(state="normal")
    update_status()

def next_round():
    if state["round"] >= 5:
        result_text.delete("1.0", tk.END)
        result_text.insert(
            tk.END,
            "HOÀN THÀNH\n\n"
            f"Mức hài lòng cuối: {state['satisfaction']:.0f}/100\n"
            f"Danh tiếng cuối: {state['reputation']:.0f}/100"
        )
        next_button.config(state="disabled")
        return
    state["round"] += 1
    show_crisis()

# 7. GUI
window = tk.Tk()
window.title("Mô phỏng Quản lý Khủng hoảng Du lịch")
window.geometry("750x700")

tk.Label(window, text="MÔ PHỎNG KHỦNG HOẢNG DU LỊCH", font=("Arial", 18, "bold")).pack(pady=10)

status = tk.Label(window, font=("Arial", 10))
status.pack(pady=5)

tk.Label(window, text="TÌNH HUỐNG", font=("Arial", 13, "bold")).pack(pady=5)

crisis_text = tk.Text(window, height=8, width=80, wrap="word")
crisis_text.pack(padx=15)

tk.Label(window, text="QUYẾT ĐỊNH CỦA BẠN", font=("Arial", 12, "bold")).pack(pady=5)

decision_entry = tk.Entry(window, width=80)
decision_entry.pack(padx=15)

tk.Label(window, text="GIẢI THÍCH", font=("Arial", 12, "bold")).pack(pady=5)

reason_text = tk.Text(window, height=4, width=80, wrap="word")
reason_text.pack(padx=15)

evaluate_button = tk.Button(
    window,
    text="ĐÁNH GIÁ QUYẾT ĐỊNH",
    command=evaluate,
    width=25
)
evaluate_button.pack(pady=8)

tk.Label(window, text="KẾT QUẢ", font=("Arial", 13, "bold")).pack(pady=5)

result_text = tk.Text(window, height=13, width=80, wrap="word")
result_text.pack(padx=15)

next_button = tk.Button(
    window,
    text="VÒNG TIẾP THEO",
    command=next_round,
    state="disabled",
    width=20
)
next_button.pack(pady=8)

# 8. Start game
update_status()
show_crisis()
window.mainloop()