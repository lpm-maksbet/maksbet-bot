import os
import discord
from discord.ext import commands
from discord.ui import Button, View

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Bazy danych
prestiz_db = {}  # user_id: int
mecze_db = {}    # id_meczu: dict
kupony_db = []   # lista słowników z kuponami

DEFAULT_PRESTIZ = 1000  # Startowy bilans
MIN_KURS = 1.14

def get_prestiz(user_id):
    if user_id not in prestiz_db:
        prestiz_db[user_id] = DEFAULT_PRESTIZ
    return prestiz_db[user_id]

# --- OFERTA ZAKŁADÓW LIGOWYCH Z KURSAMI (NA PODSTAWIE SEZONU 1) ---
OFERTA_LIGOWA = {
    "L1": {"nazwa": "Mistrz Ligi — FC Leds", "kurs": 1.75},
    "L2": {"nazwa": "Mistrz Ligi — Kocia Dynastia II", "kurs": 2.10},
    "L3": {"nazwa": "Mistrz Ligi — FC CPELE", "kurs": 3.50},
    "L4": {"nazwa": "Top 3 Ligi — Kocia Dynastia", "kurs": 2.20},
    "L5": {"nazwa": "Ostatnie Miejsce — BGV", "kurs": 1.30},
    "L6": {"nazwa": "Ostatnie Miejsce — Beryl FC", "kurs": 2.80},
    "L7": {"nazwa": "Najlepszy Atak — FC Leds", "kurs": 1.60},
    "L8": {"nazwa": "Najlepsza Obrona — FC CPELE", "kurs": 1.85},
    "S1": {"nazwa": "Suma goli w sezonie: Powyżej 90.5", "kurs": 1.45},
    "S2": {"nazwa": "Suma goli w sezonie: Poniżej 90.5", "kurs": 2.40},
    "S3": {"nazwa": "Hat-trick w sezonie: TAK", "kurs": 1.35},
    "S4": {"nazwa": "Sezon bez porażki dowolnej drużyny: TAK", "kurs": 4.50},
    "S5": {"nazwa": "Wynik 10:0 lub wyższy w meczu: TAK", "kurs": 2.10},
    "S6": {"nazwa": "Użycie VAR w finale: TAK", "kurs": 1.15}
}

@bot.event
async def on_ready():
    print(f"✅ Bot MaksBet został pomyślnie uruchomiony jako: {bot.user}")

# --- WIDOK INTERAKTYWNEGO PANELA ---

class PanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚽ Obstaw Mecz", style=discord.ButtonStyle.primary, custom_id="btn_mecz")
    async def btn_mecz(self, interaction: discord.Interaction, button: Button):
        otwarte = [
            f"🔹 **[ID: {m_id}]** {data['d1']} vs {data['d2']}\n"
            f"   Kursy: **1** (`{data['k1']}`) | **X** (`{data['kX']}`) | **2** (`{data['k2']}`)"
            for m_id, data in mecze_db.items() if data['status'] == "OTWARTY"
        ]
        
        embed = discord.Embed(title="⚽ OFERTA MECZOWA", color=discord.Color.blue())
        if not otwarte:
            embed.description = "❌ **Brak aktywnych meczów do obstawienia w tej chwili.**"
        else:
            embed.description = "\n\n".join(otwarte)
            embed.add_field(name="👉 Jak obstawić?", value="Wpisz na czacie:\n`!obstaw <ID_Meczu> <1/X/2> <kwota>`", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🏆 Obstaw Ligę", style=discord.ButtonStyle.success, custom_id="btn_liga")
    async def btn_liga(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(title="🏆 OFERTA LIGOWA — DŁUGOTERMINOWA", description="Oto wybrane zakłady na podstawie statystyk z Sezonu 1:", color=discord.Color.gold())
        
        opis_oferty = ""
        for kod, info in OFERTA_LIGOWA.items():
            opis_oferty += f"▫️ **`{kod}`** — {info['nazwa']} (Kurs: **{info['kurs']}**)\n"
            
        embed.add_field(name="📊 Wybrane Zakłady i Kursy", value=opis_oferty, inline=False)
        embed.add_field(
            name="📝 Jak postawić kupon ligowy?", 
            value="Wpisz na czacie:\n`!obstawlige <Kod1,Kod2,...> <kwota>`\n*Przykład:* `!obstawlige L1,S1,S3 200`\n*(Możesz łączyć max 10 kodów w jeden kupon!)*", 
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🎫 Twoje Kupony", style=discord.ButtonStyle.blurple, custom_id="btn_kupony")
    async def btn_kupony(self, interaction: discord.Interaction, button: Button):
        user_kupony = [k for k in kupony_db if k["user_id"] == interaction.user.id]
        
        embed = discord.Embed(title=f"🎫 Kupony gracza {interaction.user.name}", color=discord.Color.purple())
        if not user_kupony:
            embed.description = "Nie posiadasz jeszcze żadnych postawionych kuponów."
        else:
            opis = ""
            for i, k in enumerate(user_kupony[-5:], 1):  # Pokazuje 5 ostatnich
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

# --- KOMENDA !PANEL ---

@bot.command(name="panel")
async def panel(ctx):
    pts = get_prestiz(ctx.author.id)
    embed = discord.Embed(title="🎰 GŁÓWNY PANEL BUKMACHERSKI", description="Kliknij przycisk poniżej, aby wyświetlić dedykowaną sekcję!", color=discord.Color.dark_theme())
    embed.add_field(name="💳 Stan Twojego Konta", value=f"💰 **{pts} Punktów Prestiżu**", inline=False)
    embed.set_footer(text="MaksBet • Wybierz opcję")
    
    await ctx.send(embed=embed, view=PanelView())

# --- SYSTEM OBSTAWIANIA LIGI (AKUMULATOR AKO) ---

@bot.command(name="obstawlige")
async def obstawlige(ctx, kody_str: str, stawka: int):
    kody = [k.strip().upper() for k in kody_str.split(",")]
    
    # Weryfikacja liczby zdarzeń
    if len(kody) > 10:
        await ctx.send("❌ **Przekroczono limit!** Na jednym kuponie możesz połączyć maksymalnie **10 zdarzeń**.")
        return

    # Weryfikacja czy kody istnieją i kurs min 1.14
    laczny_kurs = 1.0
    nazwy_typow = []
    
    for kod in kody:
        if kod not in OFERTA_LIGOWA:
            await ctx.send(f"❌ Kod zakładu `{kod}` nie istnieje w ofercie ligowej!")
            return
        kurs = OFERTA_LIGOWA[kod]["kurs"]
        if kurs < MIN_KURS:
            await ctx.send(f"❌ Kurs zdarzenia `{kod}` ({kurs}) jest niższy niż minimalny wymagany kurs **{MIN_KURS}**!")
            return
        laczny_kurs *= kurs
        nazwy_typow.append(kod)

    pts = get_prestiz(ctx.author.id)
    if stawka <= 0 or stawka > pts:
        await ctx.send(f"❌ Nie masz tylu punktów! Twój stan konta: `{pts} PTS`.")
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
    embed.add_field(name="Stawka", value=f"`{stawka} PTS`", inline=True)
    embed.add_field(name="Ewentualna Wygrana (EWK)", value=f"💰 **{ewk} PTS**", inline=False)
    
    await ctx.send(embed=embed)

# --- MECZE ORAZ ZARZĄDZANIE PRESTIŻEM ---

@bot.command(name="dodajmecz")
@commands.has_permissions(administrator=True)
async def dodajmecz(ctx, id_meczu: str, druzyna1: str, druzyna2: str, k1: float, kX: float, k2: float):
    mecze_db[id_meczu] = {"d1": druzyna1, "d2": druzyna2, "k1": k1, "kX": kX, "k2": k2, "status": "OTWARTY"}
    await ctx.send(f"⚽ Dodano mecz **{druzyna1} vs {druzyna2}** (ID: `{id_meczu}`).")

@bot.command(name="obstaw")
async def obstaw(ctx, id_meczu: str, typ: str, stawka: int):
    typ = typ.upper()
    if id_meczu not in mecze_db or mecze_db[id_meczu]["status"] != "OTWARTY":
        await ctx.send("❌ Mecz nie istnieje lub zakłady są zamknięte!")
        return
    
    pts = get_prestiz(ctx.author.id)
    if stawka <= 0 or stawka > pts:
        await ctx.send("❌ Brak wystarczających środków!")
        return

    m = mecze_db[id_meczu]
    kurs = m["k1"] if typ == "1" else (m["kX"] if typ == "X" else m["k2"])
    if kurs < MIN_KURS:
        await ctx.send(f"❌ Kurs spotkania jest niższy niż minimalny **{MIN_KURS}**!")
        return

    ewk = int(stawka * kurs)
    prestiz_db[ctx.author.id] -= stawka
    kupony_db.append({
        "user_id": ctx.author.id,
        "typy": f"Mecz {id_meczu} ({typ})",
        "stawka": stawka,
        "kurs_laczny": kurs,
        "ewk": ewk,
        "rozliczony": False,
        "wygrany": False
    })
    await ctx.send(f"✅ Kupon postawiony! Pobrało `{stawka} PTS`. EWK: **{ewk} PTS**.")

@bot.command(name="topkaprestizu")
async def topkaprestizu(ctx):
    sorted_users = sorted(prestiz_db.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="🥇 Ranking Prestiżu (Top 10)", color=discord.Color.gold())
    description = ""
    for idx, (user_id, pts) in enumerate(sorted_users, 1):
        user = await bot.fetch_user(user_id)
        description += f"**{idx}.** {user.name} — `{pts} PTS`\n"
    embed.description = description if description else "Brak graczy."
    await ctx.send(embed=embed)

@bot.command(name="ustawprestiz")
@commands.has_permissions(administrator=True)
async def ustawprestiz(ctx, cel: str, kwota: int):
    if cel.lower() in ["@a", "all", "wszyscy"]:
        for u in prestiz_db: prestiz_db[u] = kwota
        await ctx.send(f"✅ Ustawiono `{kwota} PTS` dla WSZYSTKICH!")
    elif ctx.message.mentions:
        user = ctx.message.mentions[0]
        prestiz_db[user.id] = kwota
        await ctx.send(f"✅ Ustawiono **{kwota} PTS** dla {user.mention}.")

@bot.command(name="dodajprestiz")
@commands.has_permissions(administrator=True)
async def dodajprestiz(ctx, cel: str, kwota: int):
    if cel.lower() in ["@a", "all", "wszyscy"]:
        for u in prestiz_db: prestiz_db[u] += kwota
        await ctx.send(f"🎁 Dodano po `{kwota} PTS` dla WSZYSTKICH!")
    elif ctx.message.mentions:
        user = ctx.message.mentions[0]
        get_prestiz(user.id)
        prestiz_db[user.id] += kwota
        await ctx.send(f"🎁 Dodano **{kwota} PTS** dla {user.mention}.")

TOKEN = os.environ.get("DISCORD_TOKEN")
if TOKEN:
    bot.run(TOKEN)
