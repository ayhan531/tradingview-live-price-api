import urllib.request
import json
import time

render_token = 'rnd_vnnmI1gLoq96CQsTzrxwquKM06YH'
service_id = 'srv-datdpbm7bikc73d5t4gg'

print("Render Deploy Durumu Takip Ediliyor...")
start_time = time.time()

while time.time() - start_time < 300: # 5 dakika zaman aşımı
    req = urllib.request.Request(
        f"https://api.render.com/v1/services/{service_id}/deploys?limit=1",
        headers={"Authorization": f"Bearer {render_token}", "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if data:
                dep = data[0].get("deploy", {})
                status = dep.get("status")
                dep_id = dep.get("id")
                print(f"[{int(time.time() - start_time)}s] Deploy {dep_id} Durumu: {status}")
                if status == "live":
                    print("\n🎉 TEBRİKLER! RENDER DEPLOY TAMAMLANDI VE CANLIDA (LIVE)!")
                    break
                elif status in ["build_failed", "canceled", "deactivated"]:
                    print(f"\n❌ Deploy Başarısız: {status}")
                    break
    except Exception as e:
        print("Sorgu hatası:", e)
    time.sleep(12)
