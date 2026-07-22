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
mecze_db = {}
kupony_db = []

DEFAULT_PRESTIZ = 1000
MIN_KURS = 1.14

def get_prestiz(user_id):
    if user_id not in prestiz_db:
        prestiz_db[user_id] = DEFAULT_PRESTIZ
    return prestiz_db[user_id]

# --- ROZBUDOWANA OFERTA ZAKŁADÓW LIGOWYCH ---
OFERTA_LIGOWA = {
    # MISTRZ & PODIUM
    "M1": {"nazwa": "Mistrz Ligi — FC Leds", "kurs": 2.10},
    "M2": {"nazwa": "Mistrz Ligi — Kocia Dynastia", "kurs": 2.50},
    "M3": {"nazwa": "Mistrz Ligi — Storm Legion FC", "kurs": 3.20},
    "M4": {"nazwa": "Mistrz Ligi — FC Dynamit", "kurs": 4.50},
    "M5": {"nazwa": "Mistrz Ligi — MKS Stomil Minecraft", "kurs": 6.00},
    "M10": {"nazwa": "Mistrz Ligi — Beryl FC", "kurs": 25.00},

    # POŁOWY & CZAS ZDARZEŃ
    "P1": {"nazwa": "Więcej goli padnie w 1. połowach meczów", "kurs": 2.20},
    "P2": {"nazwa": "Więcej goli padnie w 2. połowach meczów", "kurs": 1.65},
    "P3": {"nazwa": "Równa liczba goli w obu połowach", "kurs": 3.40},
    "P4": {"nazwa": "Więcej kartek w 2. połowach meczów", "kurs": 1.45},

    # KRÓL STRZELCÓW & ASYST
    "KS1": {"nazwa": "Król Strzelców — BGVErek (Beryl FC)", "kurs": 1.80},
    "KS2": {"nazwa": "Król Strzelców — Kyranisek (FC Leds)", "kurs": 1.95},
    "KS3": {"nazwa": "Król Strzelców — George (Stomil)", "kurs": 6.50},
    "KA1": {"nazwa": "Król Asyst — M4gro_ (Pitolice)", "kurs": 2.10},
    "KA2": {"nazwa": "Król Asyst — Kyranisek (FC Leds)", "kurs": 2.25},

    # BRAMKI & OBRONA
    "G1": {"nazwa": "Suma goli w całym sezonie: Powyżej 120.5", "kurs": 1.55},
    "G2": {"nazwa": "Suma goli w całym sezonie: Poniżej 120.5", "kurs": 2.25},
    "G3": {"nazwa": "Najlepsza obrona w lidze — FC CPELE", "kurs": 1.85},
    "G4": {"nazwa": "Najsłabszy atak w lidze — BGV", "kurs": 1.30},

    # KARTKI & RZUTY ROŻNE
    "K1": {"nazwa": "Czerwone kartki w sezonie: Powyżej 3.5", "kurs": 1.80},
    "K2": {"nazwa": "Czerwone kartki w sezonie: Poniżej 3.5", "kurs": 1.90},
    "R1": {"nazwa": "Suma rzutów rożnych w sezonie: Powyżej 85.5", "kurs": 1.70},

    # SPECJALNE TAK / NIE
    "S1": {"nazwa": "Hat-trick w dowolnym meczu: TAK", "kurs": 1.30},
    "S2": {"nazwa": "Hat-trick w dowolnym meczu: NIE", "kurs": 3.20},
    "S3": {"nazwa": "Sezon bez porażki dla mistrza: TAK", "kurs": 4.50},
    "S4": {"nazwa": "Sezon bez porażki dla mistrza: NIE", "kurs": 1.18},
    "S5": {"nazwa": "Wynik 10:0 lub wyższy w meczu: TAK", "kurs": 2.10},
    "S7": {"nazwa": "Użycie VAR w finale: TAK", "kurs": 1.20}
}

@bot.event
async def on_ready():
    print(f"✅ Bot MaksBet został pomyślnie uruchomiony jako: {bot.user}")

# --- FORMULARZ / MODAL DO WPISYWANIA STAWKI ---

class ObstawFormularz(Modal, title="🎰 POSTAW KUPON LIGOWY"):
    stawka_input = TextInput(
        label="Podaj stawkę (Punkty Prestiżu):",
        placeholder="np. 200",
        min_length=1,
        max_length=6,
        required=True
    )

    def __init__(self, wybrane_kody, laczny_kurs, nazwy_typow):
        super().__init__()
        self.wybrane_kody = wybrane_kody
        self.laczny_kurs = laczny_kurs
        self.nazwy_typow = nazwy_typow

    async def on_submit(self, interaction: discord.Interaction):
        try:
            stawka = int(self.stawka_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Stawka musi być liczbą całkowitą!", ephemeral=True)
            return

        pts = get_prestiz(interaction.user.id)
        if stawka <= 0 or stawka > pts:
            await interaction.response.send_message(f"❌ Nie masz tylu punktów! Twój stan konta: `{pts} PTS`.", ephemeral=True)
            return

        ewk = int(stawka * self.laczny_kurs)
        prestiz_db[interaction.user.id] -= stawka

        kupony_db.append({
            "user_id": interaction.user.id,
            "typy": ", ".join(self.wybrane_kody),
            "stawka": stawka,
            "kurs_laczny": self.laczny_kurs,
            "ewk": ewk,
            "rozliczony": False,
            "wygrany": False
        })

        embed = discord.Embed(title="✅ KUPON LIGOWY ZASTAŁ POSTAWIONY!", color=discord.Color.green())
        embed.add_field(name="Zaznaczone typy", value="\n".join([f"• {n}" for n in self.nazwy_typow]), inline=False)
        embed.add_field(name="Łączny Kurs AKO", value=f"**{self.laczny_kurs}**", inline=True)
        embed.add_field(name="Stawka", value=f"`{stawka} PTS`", inline=True)
        embed.add_field(name="💰 Potencjalna Wygrana (EWK)", value=f"**{ewk} PTS**", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- VIEW PRZYCISKU ZATWIERDZAJĄCEGO KUPON ---

class PotwierdzKuponView(View):
    def __init__(self, wybrane_kody, laczny_kurs, nazwy_typow):
        super().__init__(timeout=120)
        self.wybrane_kody = wybrane_kody
        self.laczny_kurs = laczny_kurs
        self.nazwy_typow = nazwy_typow

    @discord.ui.button(label="💳 Postaw Ten Kupon", style=discord.ButtonStyle.success, emoji="🎰")
    async def btn_postaw(self, interaction: discord.Interaction, button: Button):
        modal = ObstawFormularz(self.wybrane_kody, self.laczny_kurs, self.nazwy_typow)
        await interaction.response.send_modal(modal)

# --- ROZWIJANA LISTA SELEKCJI ---

class LigaSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=f"{info['nazwa'][:80]} (K: {info['kurs']})", value=kod)
            for kod, info in list(OFERTA_LIGOWA.items())[:25]
        ]
        super().__init__(placeholder="👉 Wybierz zdarzenia z listy...", min_values=1, max_values=10, options=options)

    async def callback(self, interaction: discord.Interaction):
        wybrane_kody = self.values
        laczny_kurs = 1.0
        nazwy_typow = []

        for kod in wybrane_kody:
            kurs = OFERTA_LIGOWA[kod]["kurs"]
            laczny_kurs *= kurs
            nazwy_typow.append(OFERTA_LIGOWA[kod]["nazwa"])

        laczny_kurs = round(laczny_kurs, 2)

        embed = discord.Embed(title="📝 ZAZNACZONE ZAKŁADY", color=discord.Color.gold())
        embed.description = "\n".join([f"• **{n}**" for n in nazwy_typow])
        embed.add_field(name="Łączny Kurs AKO", value=f"**{laczny_kurs}**", inline=True)
        embed.add_field(
            name="👉 Co dalej?", 
            value="Kliknij poniższy przycisk **'Postaw Ten Kupon'**, wpisz stawkę i zatwierdź zakład!", 
            inline=False
        )

        view = PotwierdzKuponView(wybrane_kody, laczny_kurs, nazwy_typow)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class LigaSelectView(View):
    def __init__(self):
        super().__init__()
        self.add_item(LigaSelect())

# --- MAIN PANEL VIEW ---

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
        embed = discord.Embed(title="🏆 OFERTA LIGOWA — WYBIERZ Z LISTY", description="Zaznacz opcje w poniższym menu rozwijanym, a następnie wpisz kwotę w formularzu:", color=discord.Color.gold())
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

# --- URUCHOMIENIE WERWERA I BOTA ---
keep_alive()

TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
