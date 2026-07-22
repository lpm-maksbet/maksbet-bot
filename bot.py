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
kupony_db = []  # Lista kuponów: {'id': int, 'user_id': int, 'user_name': str, 'typy': str, 'stawka': int, 'kurs_laczny': float, 'ewk': int, 'rozliczony': bool, 'wygrany': bool}

DEFAULT_PRESTIZ = 1000
MIN_KURS = 1.14

def get_prestiz(user_id):
    if user_id not in prestiz_db:
        prestiz_db[user_id] = DEFAULT_PRESTIZ
    return prestiz_db[user_id]

# --- OFERTA BUKMACHERSKA 1. KOLEJKI (STYL STS) ---
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

# --- SYSTEM ROZLICZANIA ZAKŁADÓW DLA ADMINISTRATORA ---

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
        embed.add_field(name="Postawione Typy", value=f"```{kupon['typy']}
