import discord
from discord.ext import commands
from discord.ui import Button, View

# Konfiguracja bota
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Bazy danych w pamięci
prestiz_db = {}  # user_id: ilosc_punktow
mecze_db = {}    # id_meczu: {druzyna1, druzyna2, kurs1, kursX, kurs2, status}
ligowe_db = {}   # id_ligi: {nazwa, typy_kursy, status}
kupony_db = []   # lista postawionych kuponów

DEFAULT_PRESTIZ = 1000  # Darmowe punkty na start

def get_prestiz(user_id):
    if user_id not in prestiz_db:
        prestiz_db[user_id] = DEFAULT_PRESTIZ
    return prestiz_db[user_id]

@bot.event
async def on_ready():
    print(f"✅ Bot MaksBet został pomyślnie uruchomiony jako: {bot.user}")

# --- WIDOK PANELA Z PRZYCISKAMI ---

class PanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="⚽ Obstaw Mecz", style=discord.ButtonStyle.primary, custom_id="btn_obstaw_mecz")
    async def btn_mecz(self, interaction: discord.Interaction, button: Button):
        # Pokazuje dostępne mecze
        otwarte_mecze = [f"**ID: {m_id}** — {data['d1']} vs {data['d2']} (1: `{data['k1']}` | X: `{data['kX']}` | 2: `{data['k2']}`) " for m_id, data in mecze_db.items() if data['status'] == "OTWARTY"]
        
        if not otwarte_mecze:
            await interaction.response.send_message("❌ Baza nie posiada obecnie otwartych meczów do obstawienia!\nUżyj komendy: `!obstaw <ID_Meczu> <1/X/2> <kwota>`", ephemeral=True)
        else:
            opis = "\n".join(otwarte_mecze)
            await interaction.response.send_message(f"⚽ **DOSTĘPNE MECZE DO OBSTAWIENIA:**\n\n{opis}\n\n👉 Aby obstawić, wpisz na czacie:\n`!obstaw <ID_Meczu> <1/X/2> <kwota>`", ephemeral=True)

    @discord.ui.button(label="🏆 Obstaw Ligę", style=discord.ButtonStyle.success, custom_id="btn_obstaw_lige")
    async def btn_liga(self, interaction: discord.Interaction, button: Button):
        otwarte_ligi = [f"**ID Ligi: {l_id}** — {data['nazwa']}" for l_id, data in ligowe_db.items() if data['status'] == "OTWARTY"]
        
        if not otwarte_ligi:
            await interaction.response.send_message("🏆 Brak aktywnych zakładów ligowych w tej chwili!\nUżyj komendy: `!obstawlige <ID_Ligi> <Twój_Typ> <kwota>`", ephemeral=True)
        else:
            opis = "\n".join(otwarte_ligi)
            await interaction.response.send_message(f"🏆 **DOSTĘPNE ZAKŁADY LIGOWE:**\n\n{opis}\n\n👉 Aby obstawić, wpisz na czacie:\n`!obstawlige <ID_Ligi> <Twój_Typ> <kwota>`", ephemeral=True)

    @discord.ui.button(label="🥇 Top 10 Prestiżu", style=discord.ButtonStyle.secondary, custom_id="btn_topka")
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
    embed = discord.Embed(title="🎰 GLÓWNY PANEL BUKMACHERSKI", description="Wybierz opcję poniżej, aby wyświetlić ofertę zakładów lub sprawdzić ranking!", color=discord.Color.blue())
    embed.add_field(name="💳 Twój Stan Konta", value=f"💰 Posiadasz: **{pts} Punkty Prestiżu**", inline=False)
    embed.set_footer(text="MaksBet System • Wybierz przycisk poniżej")
    
    await ctx.send(embed=embed, view=PanelView())

# --- ZARZĄDZANIE PRESTIŻEM (DLA ADMINA) ---

@bot.command(name="ustawprestiz")
@commands.has_permissions(administrator=True)
async def ustawprestiz(ctx, cel: str, kwota: int):
    """Użycie: !ustawprestiz @gracz 5000 LUB !ustawprestiz all 5000"""
    if cel.lower() in ["@a", "all", "wszyscy"]:
        for user_id in prestiz_db:
            prestiz_db[user_id] = kwota
        await ctx.send(f"✅ **Ustawiono `{kwota} PTS` dla WSZYSTKICH zarejestrowanych graczy!**")
    elif ctx.message.mentions:
        user = ctx.message.mentions[0]
        prestiz_db[user.id] = kwota
        await ctx.send(f"✅ Ustawiono **{kwota} PTS** dla {user.mention}.")
    else:
        await ctx.send("❌ Oznacz użytkownika (`@nick`) lub wpisz `all` / `@a`!")

@bot.command(name="dodajprestiz")
@commands.has_permissions(administrator=True)
async def dodajprestiz(ctx, cel: str, kwota: int):
    """Użycie: !dodajprestiz @gracz 500 LUB !dodajprestiz all 500"""
    if cel.lower() in ["@a", "all", "wszyscy"]:
        for user_id in prestiz_db:
            prestiz_db[user_id] += kwota
        await ctx.send(f"🎁 **Dodano po `{kwota} PTS` dla WSZYSTKICH graczy!**")
    elif ctx.message.mentions:
        user = ctx.message.mentions[0]
        get_prestiz(user.id)
        prestiz_db[user.id] += kwota
        await ctx.send(f"🎁 Dodano **{kwota} PTS** użytkownikowi {user.mention}. Nowy stan: `{prestiz_db[user.id]} PTS`.")
    else:
        await ctx.send("❌ Oznacz użytkownika (`@nick`) lub wpisz `all` / `@a`!")

# --- TOPKA PRESTIŻU ---

@bot.command(name="topkaprestizu")
async def topkaprestizu(ctx):
    sorted_users = sorted(prestiz_db.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="🥇 Ranking Prestiżu (Top 10)", color=discord.Color.gold())
    
    description = ""
    for idx, (user_id, pts) in enumerate(sorted_users, 1):
        user = await bot.fetch_user(user_id)
        description += f"**{idx}.** {user.name} — `{pts} PTS`\n"
    
    embed.description = description if description else "Brak zarejestrowanych graczy."
    await ctx.send(embed=embed)

# --- BAZOWE ZARZĄDZANIE MECZAMI I ZAKŁADAMI ---

@bot.command(name="dodajmecz")
@commands.has_permissions(administrator=True)
async def dodajmecz(ctx, id_meczu: str, druzyna1: str, druzyna2: str, k1: float, kX: float, k2: float):
    mecze_db[id_meczu] = {"d1": druzyna1, "d2": druzyna2, "k1": k1, "kX": kX, "k2": k2, "status": "OTWARTY"}
    await ctx.send(f"⚽ Dodano mecz **{druzyna1} vs {druzyna2}** (ID: `{id_meczu}`). Zakłady otwarte!")

@bot.command(name="obstaw")
async def obstaw(ctx, id_meczu: str, typ: str, stawka: int):
    typ = typ.upper()
    if id_meczu not in mecze_db or mecze_db[id_meczu]["status"] != "OTWARTY":
        await ctx.send("❌ Mecz nie istnieje lub jest zamknięty!")
        return
    
    pts = get_prestiz(ctx.author.id)
    if stawka <= 0 or stawka > pts:
        await ctx.send("❌ Nie masz wystarczającej ilości punktów!")
        return

    m = mecze_db[id_meczu]
    kurs = m["k1"] if typ == "1" else (m["kX"] if typ == "X" else m["k2"])
    ewk = int(stawka * kurs)
    
    prestiz_db[ctx.author.id] -= stawka
    kupony_db.append({"user_id": ctx.author.id, "mecz_id": id_meczu, "typ": typ, "stawka": stawka, "ewk": ewk, "rozliczony": False})
    await ctx.send(f"✅ Kupon postawiony! Pobrało `{stawka} PTS`. Ewentualna wygrana: **{ewk} PTS**.")

# Twój Token:
bot.run("MTUyOTI3ODc4MTU5MDg2Mzk1Mw.GD75xM.5gVH4wFdUPGn4oywJQxztgHOHA7eaMIz7T5uuA")