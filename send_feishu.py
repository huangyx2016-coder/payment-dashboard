import json, requests, os

# Feishu credentials (from env, do not hardcode)
APP_ID = os.environ["FEISHU_APP_ID"]
APP_SECRET = os.environ["FEISHU_APP_SECRET"]

# Recipients
RECIPIENTS = [
    ("邓子平", "ou_744c1351a6b58ac8b8e259184cd1dbc8"),
    ("Mark", "ou_44d1d3cbeb2e1829ddb5fa28351ecd89"),
]

# Load data
script_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(script_dir, "data", "0827.json"), "r", encoding="utf-8") as f:
    d = json.load(f)

grandC = grandE = grandF = rows = 0
for sn, items in d["sheets"].items():
    for r in items:
        if r["A"] == "合计":
            continue
        c = r.get("C")
        e = r.get("E")
        f = r.get("F")
        if isinstance(c, (int, float)):
            grandC += c
        if isinstance(e, (int, float)):
            grandE += e
        if isinstance(f, (int, float)):
            grandF += f
        rows += 1


def fmt(n):
    sign = "-" if n < 0 else ""
    n = abs(n)
    return sign + "$" + "{:,.2f}".format(n)


msg = "💰 打款汇总 08/27\n\n"
msg += f"账户数: {rows}\n"
msg += f"最近一次已打款合计: {fmt(grandC)}\n"
msg += f"即将打款合计: {fmt(grandE)}\n"
msg += f"店铺余额合计: {fmt(grandF)}\n\n"
msg += "各 sheet 明细:\n"

for sn in ["境外账户", "耳环账户", "银饰账户", "手链", "项链.戒指"]:
    items = d["sheets"][sn]
    sc = sum(r.get("C") if isinstance(r.get("C"), (int, float)) and r["A"] != "合计" else 0 for r in items)
    se = sum(r.get("E") if isinstance(r.get("E"), (int, float)) and r["A"] != "合计" else 0 for r in items)
    sf = sum(r.get("F") if isinstance(r.get("F"), (int, float)) and r["A"] != "合计" else 0 for r in items)
    cnt = sum(1 for r in items if r["A"] != "合计")
    msg += f"  {sn}: {cnt}行 | C={fmt(sc)} | E={fmt(se)} | F={fmt(sf)}\n"

msg += f"\n查看详情: https://huangyx2016-coder.github.io/payment-dashboard/payment.html"

# Get access token
resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": APP_ID, "app_secret": APP_SECRET},
)
token = resp.json().get("tenant_access_token")
if not token:
    print("Failed to get token:", resp.text)
    exit(1)

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Send to each recipient
for name, open_id in RECIPIENTS:
    body = {
        "receive_id": open_id,
        "msg_type": "text",
        "content": json.dumps({"text": msg}),
    }
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
        headers=headers,
        json=body,
    )
    result = resp.json()
    if result.get("code") == 0:
        print(f"Sent to {name}: OK")
    else:
        print(f"Sent to {name}: FAIL - {result}")

print("\nMessage content:")
print(msg)
