import os
import threading
import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
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
kupony_db = []

DEFAULT_PRESTIZ = 1000
MIN_KURS = 1.14

def get_prestiz(user_id):
    if user_id not in prestiz_db:
        prestiz_db[user_id] = DEFAULT_PRESTIZ
    return prestiz_db[user_id]

# --- OFERTA BUKMACHERSKA 1. KOLEJKI ---
OFERTA_MECZOWA = {
    "M1": {
        "mecz": "FC Pitulice vs Niebiańskie Bractwo",
        "data": "27.07 | 14:00",
        "typy": {
            "1": {"nazwa": "Wygrana: FC Pitulice", "kurs": 1.85},
            "X": {"nazwa": "Remis", "kurs": 3.40},
            "2": {"nazwa": "Wygrana: Niebiańskie Bractwo", "kurs": 2.65},
            "1X": {"nazwa": "Podwójna szansa: FC Pitulice lub Remis", "kurs": 1.25},
            "G2.5": {"nazwa": "Liczba goli: Powyżej 2.5", "kurs": 1.55},
            "BTTS": {"nazwa": "Obie drużyny strzelą (BTTS): TAK", "kurs": 1.60},
            "ROZ8.5": {"nazwa": "Rzuty rożne: Powyżej 8.5", "kurs": 1.70},
            "KAR3.5": {"nazwa": "Żółte kartki: Powyżej 3.5", "kurs": 1.85},
            "STRZ1": {"nazwa": "M4gro_ strzeli gola", "kurs": 2.10},
            "CEL8.5": {"nazwa": "Celne strzały w meczu: Powyżej 8.5", "kurs": 1.75},
            "CK1": {"nazwa": "Czyste konto: FC Pitulice", "kurs": 2.40}
        }
    },
    "M2": {
        "mecz": "Kocia Dynastia vs Zachrystia YTS",
        "data": "27.07 | 16:00",
        "typy": {
            "1": {"nazwa": "Wygrana: Kocia Dynastia", "kurs": 1.45},
            "X": {"nazwa": "Remis", "kurs": 3.80},
            "2": {"nazwa": "Wygrana: Zachrystia YTS", "kurs": 3.60},
            "G3.5": {"nazwa": "Liczba goli: Powyżej 3.5", "kurs": 1.65},
            "BTTS": {"nazwa": "Obie drużyny strzelą (BTTS): TAK", "kurs": 1.50},
            "P1_G1.5": {"nazwa": "1. Połowa goli: Powyżej 1.5", "kurs": 1.90},
            "ROZ9.5": {"nazwa": "Rzuty rożne: Powyżej 9.5", "kurs": 1.80},
            "STRZ2": {"nazwa": "TubaSkibidik_ strzeli gola", "kurs": 1.75},
            "KAR_CZ": {"nazwa": "Czerwona kartka w meczu: TAK", "kurs": 3.10},
            "COMBO1": {"nazwa": "Kocia Dynastia wygra + Over 2.5 gola", "kurs": 1.70}
        }
    },
    "M3": {
        "mecz": "MKS Stomil Minecraft vs Storm Legion FC",
        "data": "27.07 | 18:00",
        "typy": {
            "1": {"nazwa": "Wygrana: Stomil Minecraft", "kurs": 2.20},
            "X": {"nazwa": "Remis", "kurs": 3.30},
            "2": {"nazwa": "Wygrana: Storm Legion FC", "kurs": 2.15},
            "G2.5": {"nazwa": "Liczba goli: Powyżej 2.5", "kurs": 1.70},
            "BTTS": {"nazwa": "Obie drużyny strzelą (BTTS): TAK", "kurs": 1.55},
            "STRZ3": {"nazwa": "George strzeli gola", "kurs": 1.90},
            "ASYST1": {"nazwa": "Plankton93 zaliczy asystę", "kurs": 2.30},
            "CEL10.5": {"nazwa": "Celne strzały w meczu: Powyżej 10.5", "kurs": 1.85},
            "GOL10M": {"nazwa": "Gol przed 10. minutą: TAK", "kurs": 2.80}
        }
    },
    "M4": {
        "mecz": "🔥 Beryl FC vs FC Leds (HIT KOLEJKI)",
        "data": "27.07 | 20:00",
        "typy": {
            "1": {"nazwa": "Wygrana: Beryl FC", "kurs": 4.20},
            "X": {"nazwa": "Remis", "kurs": 4.00},
            "2": {"nazwa": "Wygrana: FC Leds", "kurs": 1.30},
            "G4.5": {"nazwa": "Liczba goli: Powyżej 4.5", "kurs": 1.80},
            "STRZ4": {"nazwa": "Kyranisek strzeli gola", "kurs": 1.40},
            "STRZ5": {"nazwa": "BGVErek strzeli gola", "kurs": 1.85},
            "HAT": {"nazwa": "Kyranisek strzeli Hat-Trick", "kurs": 3.20},
            "HANDI2": {"nazwa": "Handicap: FC Leds -2.5 gola", "kurs": 2.10},
            "CK2": {"nazwa": "Czyste konto: FC Leds", "kurs": 2.15},
            "COMBO2": {"nazwa": "FC Leds wygra + Obie strzelą", "kurs": 2.25}
        }
    },
    "M5": {
        "mecz": "FC Dynamit vs FC Galaxy",
        "data": "28.07 | 14:00",
        "typy": {
            "1": {"nazwa": "Wygrana: FC Dynamit", "kurs": 1.90},
            "X": {"nazwa": "Remis", "kurs": 3.30},
            "2": {"nazwa": "Wygrana: FC Galaxy", "kurs": 2.50},
            "G2.5": {"nazwa": "Liczba goli: Powyżej 2.5", "kurs": 1.60},
            "BTTS": {"nazwa": "Obie drużyny strzelą (BTTS): TAK", "kurs": 1.50},
            "KARNY": {"nazwa": "Rzut karny w meczu: TAK", "kurs": 2.40},
            "P2_GOLI": {"nazwa": "Więcej goli w 2. połowie", "kurs": 1.65},
            "ROZ8.5": {"nazwa": "Rzuty rożne: Powyżej 8.5", "kurs": 1.75}
        }
    }
}

@bot.event
async def on_ready():
    print(f"✅ Bot MaksBet uruchomiony pomyślnie jako: {bot.user}")

# --- FORMULARZ STAWKI ---

class ObstawFormularz(Modal, title="🎰 STAWKA I POTENCJALNA WYGRANA"):
    stawka_input = TextInput(
        label="Wpisz stawkę (Punkty Prestiżu):",
        placeholder="np. 100",
        min_length=1,
        max_length=6,
        required=True
    )

    def __init__(self, typ_opis, kurs):
        super().__init__()
        self.typ_opis = typ_opis
        self.kurs = kurs

    async def on_submit(self, interaction: discord.Interaction):
        try:
            stawka = int(self.stawka_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Stawka musi być liczbą!", ephemeral=True)
            return

        pts = get_prestiz(interaction.user.id)
        if stawka <= 0 or stawka > pts:
            await interaction.response.send_message(f"❌ Brak środków! Twój stan konta: `{pts} PTS`.", ephemeral=True)
            return

        ewk = int(stawka * self.kurs)
        prestiz_db[interaction.user.id] -= stawka

        kupon_id = len(kupony_db) + 1
        kupony_db.append({
            "id": kupon_id,
            "user_id": interaction.user.id,
            "user_name": interaction.user.name,
            "typy": self.typ_opis,
            "stawka": stawka,
            "kurs_laczny": self.kurs,
            "ewk": ewk,
            "rozliczony": False,
            "wygrany": False
        })

        embed = discord.Embed(title="✅ KUPON ZOSTAŁ POSTAWIONY!", color=discord.Color.green())
        embed.add_field(name="Kupon ID", value=f"`#{kupon_id}`", inline=True)
        embed.add_field(name="Wybrany Zakład", value=f"**{self.typ_opis}**", inline=False)
        embed.add_field(name="Kurs", value=f"`{self.kurs}`", inline=True)
        embed.add_field(name="Stawka", value=f"`{stawka} PTS`", inline=True)
        embed.add_field(name="💰 Potencjalna Wygrana (EWK)", value=f"**{ewk} PTS**", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- WYBÓR ZAKŁADU DLA DANEGO MECZU ---

class MeczTypSelect(Select):
    def __init__(self, mecz_id):
        m_info = OFERTA_MECZOWA[mecz_id]
        options = [
            discord.SelectOption(label=f"{t_data['nazwa']} (Kurs: {t_data['kurs']})", value=t_kod)
            for t_kod, t_data in m_info["typy"].items()
        ]
        super().__init__(placeholder=f"👉 Wybierz rynek dla: {m_info['mecz']}", options=options)
        self.mecz_id = mecz_id

    async def callback(self, interaction: discord.Interaction):
        kod_typu = self.values[0]
        m_info = OFERTA_MECZOWA[self.mecz_id]
        t_data = m_info["typy"][kod_typu]

        opis = f"{m_info['mecz']} — {t_data['nazwa']}"
        modal = ObstawFormularz(opis, t_data['kurs'])
        await interaction.response.send_modal(modal)

class MeczTypView(View):
    def __init__(self, mecz_id):
        super().__init__()
        self.add_item(MeczTypSelect(mecz_id))

class MeczSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=f"{data['mecz']} ({data['data']})", value=m_id)
            for m_id, data in OFERTA_MECZOWA.items()
        ]
        super().__init__(placeholder="⚽ Wybierz mecz, który chcesz obstawić...", options=options)

    async def callback(self, interaction: discord.Interaction):
        mecz_id = self.values[0]
        m_info = OFERTA_MECZOWA[mecz_id]

        embed = discord.Embed(title=f"🎯 OFERTA STS: {m_info['mecz']}", color=discord.Color.blue())
        embed.description = "Wybierz interesujący Cię rynek z poniższej listy:"

        await interaction.response.send_message(embed=embed, view=MeczTypView(mecz_id), ephemeral=True)

class MeczSelectView(View):
    def __init__(self):
        super().__init__()
        self.add_item(MeczSelect())

# --- SYSTEM ROZLICZANIA ZAKŁADÓW ---

class RozliczKuponView(View):
    def __init__(self, kupon):
        super().__init__(timeout=120)
        self.kupon = kupon

    @discord.ui.button(label="✅ Wygrany", style=discord.ButtonStyle.success)
    async def btn_wygrana(self, interaction: discord.Interaction, button: Button):
        self.kupon["rozliczony"] = True
        self.kupon["wygrany"] = True
        
        user_id = self.kupon["user_id"]
        get_prestiz(user_id)
        prestiz_db[user_id] += self.kupon["ewk"]

        embed = discord.Embed(title="✅ Kupon Rozliczony jako WYGRANY!", color=discord.Color.green())
        embed.add_field(name="Gracz", value=f"**{self.kupon['user_name']}**", inline=True)
        embed.add_field(name="Wygrana Kwota", value=f"💰 **+{self.kupon['ewk']} PTS**", inline=True)
        embed.add_field(name="Kupon ID", value=f"`#{self.kupon['id']}`", inline=False)
        
        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ Przegrany", style=discord.ButtonStyle.danger)
    async def btn_przegrana(self, interaction: discord.Interaction, button: Button):
        self.kupon["rozliczony"] = True
        self.kupon["wygrany"] = False

        embed = discord.Embed(title="❌ Kupon Rozliczony jako PRZEGRANY!", color=discord.Color.red())
        embed.add_field(name="Gracz", value=f"**{self.kupon['user_name']}**", inline=True)
        embed.add_field(name="Kupon ID", value=f"`#{self.kupon['id']}`", inline=True)

        await interaction.response.edit_message(embed=embed, view=None)

class SelectKuponRozlicz(Select):
    def __init__(self, aktywne_kupony):
        options = [
            discord.SelectOption(
                label=f"Kupon #{k['id']} - {k['user_name']} ({k['stawka']} PTS)", 
                description=f"{k['typy'][:50]}...",
                value=str(k['id'])
            )
            for k in aktywne_kupony[:25]
        ]
        super().__init__(placeholder="👉 Wybierz kupon gracza do rozliczenia...", options=options)

    async def callback(self, interaction: discord.Interaction):
        kupon_id = int(self.values[0])
        kupon = next((k for k in kupony_db if k["id"] == kupon_id), None)

        if not kupon:
            await interaction.response.send_message("❌ Nie znaleziono kuponu!", ephemeral=True)
            return

        embed = discord.Embed(title=f"📋 ROZLICZANIE KUPONU #{kupon['id']}", color=discord.Color.orange())
        embed.add_field(name="Gracz", value=f"**{kupon['user_name']}**", inline=True)
        embed.add_field(name="Stawka", value=f"`{kupon['stawka']} PTS`", inline=True)
        embed.add_field(name="Ewentualna Wygrana (EWK)", value=f"💰 **{kupon['ewk']} PTS**", inline=True)
        embed.add_field(name="Postawione Typy", value=f"• {kupon['typy']}", inline=False)
        embed.add_field(name="Wybierz wynik:", value="Kliknij **✅ Wygrany** lub **❌ Przegrany** poniżej.", inline=False)

        await interaction.response.send_message(embed=embed, view=RozliczKuponView(kupon), ephemeral=True)

class RozliczSelectView(View):
    def __init__(self, aktywne_kupony):
        super().__init__()
        self.add_item(SelectKuponRozlicz(aktywne_kupony))

# --- KOMENDA STATYSTYK GRACZY DLA ADMINA (!bzmistrz) ---

@bot.command(name="bzmistrz", aliases=["statystyki"])
@commands.has_permissions(administrator=True)
async def bzmistrz(ctx):
    rozliczone = [k for k in kupony_db if k["rozliczony"]]

    if not rozliczone:
        await ctx.send("❌ **Brak rozliczonych kuponów w historii! Statystyki pojawią się po rozliczeniu zakładów.**")
        return

    stats = {}

    for k in rozliczone:
        u_name = k["user_name"]
        if u_name not in stats:
            stats[u_name] = {"wygrane": 0, "przegrane": 0}
        
        if k["wygrany"]:
            stats[u_name]["wygrane"] += 1
        else:
            stats[u_name]["przegrane"] += 1

    embed = discord.Embed(
        title="🏆 STATYSTYKI TYPERÓW (WIN RATIO)", 
        description="Zestawienie wyników graczy i skuteczności typowania:\n", 
        color=discord.Color.purple()
    )

    opis = ""
    for idx, (name, data) in enumerate(stats.items(), 1):
        w = data["wygrane"]
        p = data["przegrane"]
        lacznie = w + p
        win_ratio = round((w / lacznie) * 100, 1) if lacznie > 0 else 0.0

        opis += f"**{idx}. {name}**\n   └ 🟢 Wygrane: `{w}` | 🔴 Przegrane: `{p}` | 📊 Win Ratio: **{win_ratio}%**\n\n"

    embed.description = opis
    embed.set_footer(text="MaksBet Admin System • Statystyki Gracz vs Bukmacher")
    await ctx.send(embed=embed)

# --- KOMENDA POMOCY DLA ADMINA (!bzpomoc) ---

@bot.command(name="bzpomoc")
@commands.has_permissions(administrator=True)
async def bzpomoc(ctx):
    embed = discord.Embed(
        title="👑 PANEL ZARZĄDZANIA BOTEAM — KOMENDY ADMINA", 
        description="Oto lista wszystkich komend administracyjnych w bota MaksBet:", 
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="🎫 Rozliczanie & Statystyki",
        value=(
            "• `!pokazzaklady` (lub `!rozlicz`) — Otwiera GUI do przeglądania i rozliczania aktywnych kuponów graczy.\n"
            "• `!bzmistrz` (lub `!statystyki`) — Wyświetla wygrane, przegrane i procentowe Win Ratio wszystkich typerów."
        ),
        inline=False
    )
    
    embed.add_field(
        name="💰 Zarządzanie Prestiżem",
        value=(
            "• `!ustawprestiz <@gracz/all> <kwota>` — Ustawia określoną liczbę punktów dla gracza lub wszystkich.\n"
            "• `!dodajprestiz <@gracz/all> <kwota>` — Dodaje wybraną liczbę punktów wskazanemu graczowi lub wszystkim."
        ),
        inline=False
    )

    embed.set_footer(text="MaksBet Admin System • Dostępne tylko dla Administracji")
    await ctx.send(embed=embed)

# --- KOMENDA !POKAZZAKLADY ---

@bot.command(name="pokazzaklady", aliases=["rozlicz"])
@commands.has_permissions(administrator=True)
async def pokazzaklady(ctx):
    aktywne_kupony = [k for k in kupony_db if not k["rozliczony"]]

    if not aktywne_kupony:
        await ctx.send("❌ **Brak aktywnych (nierozliczonych) kuponów w systemie.**")
        return

    embed = discord.Embed(title="⚙️ PANEL ROZLICZANIA ZAKŁADÓW (ADMIN)", description="Wybierz z listy poniżej kupon gracza, który chcesz rozliczyć:", color=discord.Color.gold())
    await ctx.send(embed=embed, view=RozliczSelectView(aktywne_kupony))

# --- GŁÓWNY PANEL BOTA ---

class PanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚽ Obstaw Mecz (Rynki STS)", style=discord.ButtonStyle.primary, custom_id="btn_mecz")
    async def btn_mecz(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🎯 ZAKŁADY MECZOWE 1. KOLEJKI (STYL STS)", 
            description="Wybierz spotkanie z poniższego menu rozwijanego, aby zobaczyć pełną ofertę rynków:", 
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=MeczSelectView(), ephemeral=True)

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
                opis += f"**{i}. [{status}]** Kupon `#{k['id']}` | `{k['typy']}` | Stawka: `{k['stawka']} PTS` | EWK: **{k['ewk']} PTS**\n"
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
    embed = discord.Embed(title="🎰 GŁÓWNY PANEL BUKMACHERSKI MAKSBET", description="Kliknij przycisk poniżej, aby otworzyć ofertę!", color=discord.Color.dark_theme())
    embed.add_field(name="💳 Stan Twojego Konta", value=f"💰 **{pts} Punktów Prestiżu**", inline=False)
    embed.set_footer(text="MaksBet • Wybierz opcję")
    await ctx.send(embed=embed, view=PanelView())

# --- URUCHOMIENIE SERWERA I BOTA ---
keep_alive()

TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
