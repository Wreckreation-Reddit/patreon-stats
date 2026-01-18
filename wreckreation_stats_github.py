# Wreckreation Patreon Stats

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from PIL import Image, ImageDraw, ImageFont
import time
import re
import requests
import base64
from datetime import datetime
import os
import csv
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════
PATREON_URL = "https://www.patreon.com/cw/u10680381"

GITHUB_USERNAME = "Wreckreation-Reddit"
GITHUB_REPO = "patreon-stats"
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # Pulled from secrets
GITHUB_FILE_PATH = "stats.png"
GITHUB_GRAPH_PATH = "stats_graph.png"
GITHUB_CSV_PATH = "stats_history.csv"

IMAGE_SAVE_PATH = "stats.png"
GRAPH_SAVE_PATH = "stats_graph.png"
CSV_SAVE_PATH = "stats_history.csv"

# ═══════════════════════════════════════════════════════════
# STEP 1: SCRAPE PATREON STATS
# ═══════════════════════════════════════════════════════════
print("="*60)
print("WRECKREATION PATREON STATS UPDATER (GitHub Actions)")
print("="*60)

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920,1080')

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get(PATREON_URL)

print("\n[1/5] Scraping Patreon...")
time.sleep(5)

try:
    close_buttons = driver.find_elements(By.XPATH, "//button[@aria-label='Close Dialog']")
    if close_buttons:
        close_buttons[0].click()
        time.sleep(0.5)
except:
    pass

try:
    span = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "truncated-summary-text"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", span)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", span)
    time.sleep(3)
    
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'paid members')]"))
    )
    
    full_text = driver.page_source
    stats_divs = driver.find_elements(By.CLASS_NAME, "cm-rhTxPu")
    stats_text = None
    for div in stats_divs:
        div_text = div.text
        if "members" in div_text and "paid members" in div_text:
            stats_text = div_text
            break
    
    search_text = stats_text if stats_text else full_text
    
    members_match = re.search(r"(\d{1,3}(?:,\d{3})*)\s*members", search_text)
    paid_match = re.search(r"(\d{1,3}(?:,\d{3})*)\s*paid members", search_text)
    earnings_match = re.search(r"\$(\d{1,3}(?:,\d{3})*)\s*/\s*month", search_text)
    
    members = members_match.group(1) if members_match else "???"
    paid = paid_match.group(1) if paid_match else "???"
    earnings = earnings_match.group(1) if earnings_match else "???"
    
    members_int = int(members.replace(',', '')) if members != "???" else 0
    paid_int = int(paid.replace(',', '')) if paid != "???" else 0
    earnings_int = int(earnings.replace(',', '')) if earnings != "???" else 0
    
    print(f"   ✓ Members: {members}")
    print(f"   ✓ Paid: {paid}")
    print(f"   ✓ Earnings: ${earnings}/mo")
    
    driver.quit()

except Exception as e:
    print(f"   ✗ Error scraping: {e}")
    driver.quit()
    exit()

# ═══════════════════════════════════════════════════════════
# STEP 2: LOG DATA TO CSV
# ═══════════════════════════════════════════════════════════
print("\n[2/5] Logging data to CSV...")

now = datetime.now()
timestamp = now.strftime("%m/%d/%Y %I:%M%p PST")
timestamp_full = now.strftime("%Y-%m-%d %H:%M")

csv_exists = os.path.exists(CSV_SAVE_PATH)

with open(CSV_SAVE_PATH, 'a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    
    if not csv_exists:
        writer.writerow(['timestamp', 'members', 'paid', 'earnings'])
        print("   ✓ Created new CSV file")
    
    writer.writerow([timestamp_full, members_int, paid_int, earnings_int])
    print(f"   ✓ Logged data")

# ═══════════════════════════════════════════════════════════
# STEP 3: GENERATE GRAPH
# ═══════════════════════════════════════════════════════════
print("\n[3/5] Generating graph...")

try:
    timestamps = []
    members_history = []
    paid_history = []
    earnings_history = []
    
    with open(CSV_SAVE_PATH, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            timestamps.append(datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M"))
            members_history.append(int(row['members']))
            paid_history.append(int(row['paid']))
            earnings_history.append(int(row['earnings']))
    
    if len(timestamps) > 1:
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        fig.patch.set_facecolor('#1a1a1a')
        
        ax1.plot(timestamps, members_history, color='#00d4ff', linewidth=2, label='Total Members', marker='o')
        ax1.plot(timestamps, paid_history, color='#00ff88', linewidth=2, label='Paid Members', marker='s')
        ax1.set_ylabel('Members', fontsize=12, color='white')
        ax1.set_title('Three Fields Entertainment - Patreon Growth', fontsize=14, color='white', pad=20)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.2)
        ax1.set_facecolor('#0a0a0a')
        
        ax2.plot(timestamps, earnings_history, color='#ffcc00', linewidth=2, label='Monthly Earnings', marker='D')
        ax2.set_xlabel('Date', fontsize=12, color='white')
        ax2.set_ylabel('Earnings ($)', fontsize=12, color='white')
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.2)
        ax2.set_facecolor('#0a0a0a')
        
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.tick_params(colors='white')
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        plt.savefig(GRAPH_SAVE_PATH, dpi=150, facecolor='#1a1a1a')
        plt.close()
        
        print(f"   ✓ Graph generated")
    else:
        print("   ⚠ Only 1 data point, skipping graph")

except Exception as e:
    print(f"   ⚠ Graph generation failed: {e}")

# ═══════════════════════════════════════════════════════════
# STEP 4: CREATE STATS IMAGE
# ═══════════════════════════════════════════════════════════
print("\n[4/5] Generating stats image...")

WIDTH = 400
HEIGHT = 280
BG_COLOR = "#1a1a1a"
TEXT_COLOR = "#ffffff"
ACCENT_COLOR = "#00d4ff"

img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)

font_size_title = 24
font_size_stat = 20
font_size_label = 14
font_size_update = 12

try:
    from PIL import ImageFont
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size_title)
    stat_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size_stat)
    label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size_label)
    update_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size_update)
except:
    title_font = ImageFont.load_default()
    stat_font = ImageFont.load_default()
    label_font = ImageFont.load_default()
    update_font = ImageFont.load_default()

draw.rectangle([(0, 0), (WIDTH, 50)], fill=ACCENT_COLOR)
draw.text((WIDTH/2, 25), "Three Fields Entertainment", 
          fill=BG_COLOR, font=title_font, anchor="mm")

try:
    icon_size = (24, 24)
    total_icon = Image.open("icons/total.png").resize(icon_size)
    paid_icon = Image.open("icons/paid.png").resize(icon_size)
    month_icon = Image.open("icons/month.png").resize(icon_size)
    
    y_pos = 80
    
    # Total Members
    img.paste(total_icon, (30, y_pos - 2), total_icon if total_icon.mode == 'RGBA' else None)
    draw.text((65, y_pos), "Members:", fill=TEXT_COLOR, font=label_font)
    draw.text((WIDTH - 30, y_pos), members, fill=ACCENT_COLOR, font=stat_font, anchor="rm")
    
    y_pos += 50
    
    # Paid Members
    img.paste(paid_icon, (30, y_pos - 2), paid_icon if paid_icon.mode == 'RGBA' else None)
    draw.text((65, y_pos), "Paid Members:", fill=TEXT_COLOR, font=label_font)
    draw.text((WIDTH - 30, y_pos), paid, fill=ACCENT_COLOR, font=stat_font, anchor="rm")
    
    y_pos += 50
    
    # Monthly Earnings
    img.paste(month_icon, (30, y_pos - 2), month_icon if month_icon.mode == 'RGBA' else None)
    draw.text((65, y_pos), "Monthly Earnings:", fill=TEXT_COLOR, font=label_font)
    draw.text((WIDTH - 30, y_pos), f"${earnings}", fill=ACCENT_COLOR, font=stat_font, anchor="rm")

except Exception as e:
    # Fallback if icons don't load
    print(f"   ⚠ Couldn't load icons: {e}")
    y_pos = 80
    draw.text((30, y_pos), "Members:", fill=TEXT_COLOR, font=label_font)
    draw.text((WIDTH - 30, y_pos), members, fill=ACCENT_COLOR, font=stat_font, anchor="rm")
    
    y_pos += 50
    draw.text((30, y_pos), "Paid Members:", fill=TEXT_COLOR, font=label_font)
    draw.text((WIDTH - 30, y_pos), paid, fill=ACCENT_COLOR, font=stat_font, anchor="rm")
    
    y_pos += 50
    draw.text((30, y_pos), "Monthly Earnings:", fill=TEXT_COLOR, font=label_font)
    draw.text((WIDTH - 30, y_pos), f"${earnings}", fill=ACCENT_COLOR, font=stat_font, anchor="rm")

# Footer
draw.rectangle([(0, HEIGHT-30), (WIDTH, HEIGHT)], fill="#0a0a0a")
draw.text((WIDTH/2, HEIGHT-15), f"Updated: {timestamp}", 
          fill="#888888", font=update_font, anchor="mm")

img.save(IMAGE_SAVE_PATH)
print(f"   ✓ Stats image generated")

# ═══════════════════════════════════════════════════════════
# STEP 5: UPDATE TEXT FILE
# ═══════════════════════════════════════════════════════════
print("\n[5/5] Creating text file...")

stats_text_content = f"""Three Fields Entertainment - Patreon Stats
Last Updated: {timestamp}

Members: {members}
Paid Members: {paid}
Monthly Earnings: ${earnings}

---
Auto-generated by Wreckreation Stats Bot
"""

with open("stats.txt", "w") as f:
    f.write(stats_text_content)

print("   ✓ Text file created")

# ═══════════════════════════════════════════════════════════
# DONE
# ═══════════════════════════════════════════════════════════
print("\n" + "="*60)
print("✓ Complete! Files ready for commit")
print("="*60)
