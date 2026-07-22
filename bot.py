import os
import threading
import discord
from discord.ext import commands
from discord.ui import Button, View, Select
from flask import Flask

# --- MINI SERWER HTTP DLA RENDERA ---
app = Flask('')

@app.route('/')
def home():
    return "Bot MaksBet dziala!"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_http)
    t.start()

# --- KONFIGURACJA BOTA DISCORD ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

prestiz_db = {}
mecze_db = {}
kupony_db = []

DEFAULT_PRESTIZ = 1000
MIN_KURS = 1.14

def get_prestiz(user_id):
    if user_id not in prestiz_db:
        prestiz_db[user_id] = DEFAULT_PRESTIZ
    return prestiz_db[user_id]

# --- OFERTA LIGOWA ---
OFERTA_LIGOWA = {
    "M1": {"nazwa": "Mistrz Ligi — FC Leds", "kurs": 2.10},
    "M2": {"nazwa": "Mistrz Ligi — Kocia Dynastia", "kurs": 2.50},
    "M3": {"nazwa": "Mistrz Ligi — Storm Legion FC", "kurs": 3.20},
    "M4": {"nazwa": "Mistrz Ligi — FC Dynamit", "kurs": 4.50},
    "M5": {"nazwa": "Mistrz Ligi — MKS Stomil Minecraft", "kurs": 6.00},
    "M10": {"nazwa": "Mistrz Ligi — Beryl FC", "kurs": 25.00},
    "KS1": {"nazwa": "Król Strzelców — BGVErek (Beryl FC)", "kurs": 1.80},
    "KS2": {"nazwa": "Król Strzelców — Kyranisek (FC Leds)", "kurs": 1.95},
    "KA1": {"nazwa": "Król Asyst — M4gro_ (Pitolice)", "kurs": 2.10},
    "KA2": {"nazwa": "Król Asyst — Kyranisek (FC Leds)", "kurs": 2.25},
    "T1": {"nazwa": "Górna połowa tabeli (Top 5) — FC Leds", "kurs": 1.20},
    "G1": {"nazwa": "Więcej goli padnie w 2. połowach meczów", "kurs": 1.65},
    "S1": {"nazwa": "Hat-trick w dowolnym meczu: TAK", "kurs": 1.30},
    "S7": {"nazwa": "Użycie VAR w finale: TAK", "kurs": 1.20},
}

@bot.event
async def on_ready():
    print(f"✅ Bot MaksBet został pomyślnie uruchomiony jako: {bot.user}")

class LigaSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=f"{info['nazwa'][:80]} (K: {info['kurs']})", value=kod)
            for kod, info in list(OFERTA_LIGOWA.items())[:25]
        ]
        super().__init__(placeholder="👉 Wybierz zakłady z listy...", min_values=1, max_values=10, options=options)

    async def callback(self, interaction: discord.Interaction):
        wybrane_kody = self.values
        laczny_kurs = 1.0
        nazwy_typow = []

        for kod in wybrane_kody:
            kurs = OFERTA_LIGOWA[kod]["kurs"]
            laczny_kurs *= kurs
            nazwy_typow.append(OFERTA_LIGOWA[kod]["nazwa"])

        laczny_kurs = round(laczny_kurs, 2)

        embed = discord.Embed(title="📝 ZAZNACZONE ZAKŁADY", color=discord.Color.green())
        embed.description = "\n".join([f"• **{n}**" for n in nazwy_typow])
        embed.add_field(name="Łączny Kurs AKO", value=f"**{laczny_kurs}**", inline=True)
        embed.add_field(
            name="👉 Jak to obstawić?", 
            value=f"Wpisz na czacie:\n`!obstawlige {','.join(wybrane_kody)} <kwota>`", 
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

class LigaSelectView(View):
    def __init__(self):
        super().__init__()
        self.add_item(LigaSelect())

class PanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚽ Obstaw Mecz", style=discord.ButtonStyle.primary, custom_id="btn_mecz")
    async def btn_mecz(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="🎯 DOSTĘPNE ZAKŁADY MECZOWE", color=discord.Color.blue())
        otwarte_mecze = []
        for m_id, data in mecze_db.items():
            if data['status'] == "OTWARTY":
                m_info = (
                    f"⚔️ **[ID: {m_id}] {data['d1']} vs {data['d2']}**\n"
                    f"▫️ **1X2:** 1: `{data['k1']}` | X: `{data['kX']}` | 2: `{data['k2']}`\n"
                )
                if "opcje" in data and data["opcje"]:
                    m_info += f"▫️ **Inne rynki:** {data['opcje']}\n"
                otwarte_mecze.append(m_info)

        if not otwarte_mecze:
            embed.description = "❌ **Brak otwartych meczów w tej chwili.**"
        else:
            embed.description = "\n".join(otwarte_mecze)
            embed.add_field(
                name="👉 Jak obstawić?", 
                value="**Główny zakład (1X2):**\n`!obstaw <ID_Meczu> <1/X/2> <kwota>`\n\n**Zakład specjalny:**\n`!obstawmecz <ID_Meczu> <NazwaTypu> <Kurs> <Kwota>`", 
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🏆 Obstaw Ligę", style=discord.ButtonStyle.success, custom_id="btn_liga")
    async def btn_liga(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="🏆 OFERTA LIGOWA — WYBIERZ W OKIENKU", description="Wybierz z poniższej rozwijanej listy zakłady, które chcesz dodać do kuponu:", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, view=LigaSelectView(), ephemeral=True)

    @discord.ui.button(label="🎫 Twoje Kupony", style=discord.ButtonStyle.blurple, custom_id="btn_kupony")
    async def btn_kupony(self, interaction: discord.Interaction, button: Button):
        user_kupony = [k for k in kupony_db if k["user_id"] == interaction.user.id]
        embed = discord.Embed(title=f"🎫 Kupony gracza {interaction.user.name}", color=discord.Color.purple())
        if not user_kupony:
            embed.description = "Nie posiadasz jeszcze żadnych postawionych kuponów."
        else:
            opis = ""
            for i, k in enumerate(user_kupony[-5:], 1):
                status = "⏳ W TRAKCIE" if not k["rozliczony"] else ("✅ WYGRANY" if k["wygrany"] else "❌ PRZEGRANY")
                opis += f"**{i}. [{status}]** Typy: `{k['typy']}` | Stawka: `{k['stawka']} PTS` | EWK: **{k['ewk']} PTS**\n"
            embed.description = opis
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🥇 Top 10 Prestiżu", style=discord.ButtonStyle.secondary, custom_id="btn_top")
    async def btn_top(self, interaction: discord.Interaction, button: Button):
        sorted_users = sorted(prestiz_db.items(), key=lambda x: x[1], reverse=True)[:10]
        description = ""
        for idx, (user_id, pts) in enumerate(sorted_users, 1):
            user = await bot.fetch_user(user_id)
            description += f"**{idx}.** {user.name} — `{pts} PTS`\n"
        
        embed = discord.Embed(title="🥇 Ranking Prestiżu (Top 10)", description=description if description else "Brak graczy.", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="panel")
async def panel(ctx):
    pts = get_prestiz(ctx.author.id)
    embed = discord.Embed(title="🎰 GŁÓWNY PANEL BUKMACHERSKI", description="Kliknij przycisk poniżej, aby wyświetlić ofertę zakładową!", color=discord.Color.dark_theme())
    embed.add_field(name="💳 Stan Twojego Konta", value=f"💰 **{pts} Punktów Prestiżu**", inline=False)
    embed.set_footer(text="MaksBet • Wybierz opcję")
    await ctx.send(embed=embed, view=PanelView())

@bot.command(name="obstawlige")
async def obstawlige(ctx, kody_str: str, stawka: int):
    kody = [k.strip().upper() for k in kody_str.split(",")]
    if len(kody) > 10:
        await ctx.send("❌ **Przekroczono limit!** Maksymalnie 10 zdarzeń.")
        return

    laczny_kurs = 1.0
    nazwy_typow = []
    
    for kod in kody:
        if kod not in OFERTA_LIGOWA:
            await ctx.send(f"❌ Kod `{kod}` nie istnieje!")
            return
        kurs = OFERTA_LIGOWA[kod]["kurs"]
        if kurs < MIN_KURS:
            await ctx.send(f"❌ Kurs zdarzenia `{kod}` jest za niski!")
            return
        laczny_kurs *= kurs
        nazwy_typow.append(kod)

    pts = get_prestiz(ctx.author.id)
    if stawka <= 0 or stawka > pts:
        await ctx.send(f"❌ Brak środków! Masz: `{pts} PTS`.")
        return

    laczny_kurs = round(laczny_kurs, 2)
    ewk = int(stawka * laczny_kurs)
    
    prestiz_db[ctx.author.id] -= stawka
    kupony_db.append({
        "user_id": ctx.author.id,
        "typy": ", ".join(nazwy_typow),
        "stawka": stawka,
        "kurs_laczny": laczny_kurs,
        "ewk": ewk,
        "rozliczony": False,
        "wygrany": False
    })
    
    embed = discord.Embed(title="✅ KUPON LIGOWY POSTAWIONY!", color=discord.Color.green())
    embed.add_field(name="Wybrane typy", value=f"`{', '.join(nazwy_typow)}`", inline=False)
    embed.add_field(name="Łączny Kurs AKO", value=f"**{laczny_kurs}**", inline=True)
    embed.add_field(name="Stawka / EWK", value=f"`{stawka} PTS` ➔ **{ewk} PTS**", inline=True)
    await ctx.send(embed=embed)

# --- URUCHOMIENIE WEB SERVERA I BOTA ---
keep_alive()

TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
