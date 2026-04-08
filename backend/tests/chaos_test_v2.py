"""
CHAOS TEST - Pipeline V2 Simulazione Utente Caotico
Testa: spam click, refresh, timer edge, stale lock, multi-tab, rete instabile
"""
import asyncio, aiohttp, json, time, sys
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

API = "http://localhost:8001"
MONGO = "mongodb+srv://fandrex1_db_user:Cineworld123@cluster0.6q21tmr.mongodb.net/cineworld?retryWrites=true&w=majority"
EMAIL = "fandrex1@gmail.com"
PWD = "Fandrel2776"

results = {"pass": 0, "fail": 0, "details": []}

def log(test, ok, msg=""):
    status = "PASS" if ok else "FAIL"
    results["pass" if ok else "fail"] += 1
    results["details"].append(f"[{status}] {test}: {msg}")
    print(f"  {'✓' if ok else '✗'} {test}: {msg}")

async def login(session):
    for attempt in range(3):
        try:
            async with session.post(f"{API}/api/auth/login", json={"email": EMAIL, "password": PWD}, timeout=aiohttp.ClientTimeout(total=15)) as r:
                text = await r.text()
                if r.status == 200 and text:
                    d = json.loads(text)
                    return d["access_token"]
        except Exception:
            pass
        await asyncio.sleep(2)
    raise Exception("Login failed after 3 attempts")

async def api_post(session, token, path, body=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        async with session.post(f"{API}/api/pipeline-v2{path}", json=body, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
            return r.status, await r.json(content_type=None)
    except Exception as e:
        return 0, {"detail": str(e)}

async def api_get(session, token, path):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with session.get(f"{API}/api/pipeline-v2{path}", headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as r:
            return r.status, await r.json(content_type=None)
    except Exception as e:
        return 0, {"detail": str(e)}

async def force_timer(db, pid, field, past=True):
    t = (datetime.now(timezone.utc) - timedelta(hours=1 if past else -1)).isoformat()
    await db.film_projects.update_one({"id": pid}, {"$set": {f"pipeline_timers.{field}": t}})

async def create_test_film(session, token, title):
    s, d = await api_post(session, token, "/films", {"title": title, "genre": "action", "subgenre": "Spy"})
    pid = d["film"]["id"]
    await api_post(session, token, f"/films/{pid}/save-idea", {
        "title": title, "genre": "action", "subgenre": "Spy", "subgenres": ["Spy"],
        "pre_trama": "Un agente segreto deve infiltrarsi in una organizzazione criminale che controlla il traffico di armi nel Mediterraneo. La missione diventa personale quando scopre che il capo e suo fratello gemello separato alla nascita.",
    })
    return pid

async def advance_to_state(session, token, db, pid, target):
    """Advance film to a specific state quickly"""
    states_sequence = [
        ("idea", "propose", None),
        ("proposed", "setup-hype", {"duration_hours": 2, "strategy": "sprint"}),
        ("hype_setup", "launch-hype", None),
        ("hype_live", "complete-hype", None),
        ("casting_live", None, None),  # needs cast selection + lock
        ("prep", None, None),  # needs save-prep + start-ciak
        ("shooting", "complete-ciak", None),
        ("postproduction", "complete-finalcut", None),
        ("sponsorship", "save-sponsors", {"sponsors": []}),
        ("marketing", "choose-direct-release", None),
        ("release_pending", "release", None),
    ]
    
    for state, endpoint, body in states_sequence:
        s, d = await api_get(session, token, f"/films/{pid}")
        current = d["film"]["pipeline_state"]
        if current == target:
            return
        
        if state == "hype_live" and current == "hype_live":
            await force_timer(db, pid, "hype_end")
        elif state == "shooting" and current == "shooting":
            await force_timer(db, pid, "shooting_end")
        elif state == "postproduction" and current == "postproduction":
            await force_timer(db, pid, "postprod_end")
        
        if current == "casting_live":
            for i in range(3):
                role = "director" if i == 0 else "actor"
                await api_post(session, token, f"/films/{pid}/select-cast", {"proposal_index": i, "role": role})
            await api_post(session, token, f"/films/{pid}/lock-cast")
            s2, d2 = await api_get(session, token, f"/films/{pid}")
            if d2["film"]["pipeline_state"] == target:
                return
            current = d2["film"]["pipeline_state"]
        
        if current == "prep":
            await api_post(session, token, f"/films/{pid}/save-prep", {"equipment": [], "cgi_packages": [], "vfx_packages": [], "extras_count": 100})
            await api_post(session, token, f"/films/{pid}/start-ciak")
            s2, d2 = await api_get(session, token, f"/films/{pid}")
            if d2["film"]["pipeline_state"] == target:
                return
            current = d2["film"]["pipeline_state"]
        
        if endpoint and current == state:
            await api_post(session, token, f"/films/{pid}/{endpoint}", body)


# ═══════════════════════════════════════════════════════════════
#  TEST 1: SPAM CLICK AGGRESSIVO (10 chiamate concorrenti)
# ═══════════════════════════════════════════════════════════════
async def test_spam_click(session, token, db):
    print("\n═══ TEST 1: SPAM CLICK AGGRESSIVO ═══")
    pid = await create_test_film(session, token, "Chaos Spam Test")
    
    # Spam "propose" 10 times concurrently
    tasks = [api_post(session, token, f"/films/{pid}/propose") for _ in range(10)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    successes = [r for r in responses if not isinstance(r, Exception) and r[0] == 200]
    errors_423 = [r for r in responses if not isinstance(r, Exception) and r[0] == 423]
    errors_400 = [r for r in responses if not isinstance(r, Exception) and r[0] == 400]
    
    # Check final state
    _, d = await api_get(session, token, f"/films/{pid}")
    state = d["film"]["pipeline_state"]
    
    log("Spam propose: stato finale coerente", state == "proposed", f"state={state}")
    log("Spam propose: nessun doppio avanzamento", state != "hype_setup", f"state={state}")
    log("Spam propose: almeno 1 successo", len(successes) >= 1, f"{len(successes)} ok, {len(errors_423)} locked, {len(errors_400)} already")
    
    # Spam setup-hype
    tasks2 = [api_post(session, token, f"/films/{pid}/setup-hype", {"duration_hours": 2, "strategy": "sprint"}) for _ in range(10)]
    responses2 = await asyncio.gather(*tasks2, return_exceptions=True)
    _, d2 = await api_get(session, token, f"/films/{pid}")
    state2 = d2["film"]["pipeline_state"]
    log("Spam setup-hype: stato coerente", state2 == "hype_setup", f"state={state2}")
    
    # Spam launch-hype
    tasks3 = [api_post(session, token, f"/films/{pid}/launch-hype") for _ in range(10)]
    responses3 = await asyncio.gather(*tasks3, return_exceptions=True)
    _, d3 = await api_get(session, token, f"/films/{pid}")
    state3 = d3["film"]["pipeline_state"]
    log("Spam launch-hype: stato coerente", state3 == "hype_live", f"state={state3}")
    
    await cleanup(db, pid)
    return True


# ═══════════════════════════════════════════════════════════════
#  TEST 2: REFRESH IMMEDIATO (azione + read)
# ═══════════════════════════════════════════════════════════════
async def test_refresh(session, token, db):
    print("\n═══ TEST 2: REFRESH IMMEDIATO ═══")
    pid = await create_test_film(session, token, "Chaos Refresh Test")
    
    # Propose then immediately read
    await api_post(session, token, f"/films/{pid}/propose")
    _, d = await api_get(session, token, f"/films/{pid}")
    log("Refresh dopo propose: stato coerente", d["film"]["pipeline_state"] == "proposed", d["film"]["pipeline_state"])
    
    # Setup hype then immediately read
    await api_post(session, token, f"/films/{pid}/setup-hype", {"duration_hours": 2, "strategy": "bilanciata"})
    _, d2 = await api_get(session, token, f"/films/{pid}")
    log("Refresh dopo setup-hype: stato coerente", d2["film"]["pipeline_state"] == "hype_setup", d2["film"]["pipeline_state"])
    log("Refresh: pipeline_locked=False dopo completamento", d2["film"]["pipeline_locked"] == False, str(d2["film"]["pipeline_locked"]))
    
    # List films should include this film
    _, d3 = await api_get(session, token, "/films")
    found = any(f["id"] == pid for f in d3.get("films", []))
    log("Refresh lista: film presente", found)
    
    await cleanup(db, pid)


# ═══════════════════════════════════════════════════════════════
#  TEST 3: NAVIGAZIONE RAPIDA (GET film, POST, GET di nuovo)
# ═══════════════════════════════════════════════════════════════
async def test_navigation(session, token, db):
    print("\n═══ TEST 3: NAVIGAZIONE RAPIDA ═══")
    pid = await create_test_film(session, token, "Chaos Nav Test")
    await api_post(session, token, f"/films/{pid}/propose")
    
    # Simulate: user clicks setup-hype, navigates away, comes back
    await api_post(session, token, f"/films/{pid}/setup-hype", {"duration_hours": 3, "strategy": "costruzione_lenta"})
    
    # "Navigate away" = just don't read for a bit
    await asyncio.sleep(0.5)
    
    # "Come back" = GET film
    _, d = await api_get(session, token, f"/films/{pid}")
    film = d["film"]
    log("Nav: stato preservato", film["pipeline_state"] == "hype_setup", film["pipeline_state"])
    log("Nav: strategia preservata", film.get("hype_strategy") == "costruzione_lenta", film.get("hype_strategy"))
    log("Nav: metriche preservate", film.get("pipeline_metrics", {}).get("target_agencies", 0) > 0, str(film.get("pipeline_metrics", {}).get("target_agencies")))
    
    await cleanup(db, pid)


# ═══════════════════════════════════════════════════════════════
#  TEST 4: TIMER EDGE CASE (azione mentre timer scade)
# ═══════════════════════════════════════════════════════════════
async def test_timer_edge(session, token, db):
    print("\n═══ TEST 4: TIMER EDGE CASE ═══")
    pid = await create_test_film(session, token, "Chaos Timer Test")
    await api_post(session, token, f"/films/{pid}/propose")
    await api_post(session, token, f"/films/{pid}/setup-hype", {"duration_hours": 2, "strategy": "sprint"})
    await api_post(session, token, f"/films/{pid}/launch-hype")
    
    # Timer NOT expired: complete should fail
    s, d = await api_post(session, token, f"/films/{pid}/complete-hype")
    log("Timer attivo: complete bloccato", s == 400, f"status={s}")
    
    # Force timer to JUST expired (1 second ago)
    just_past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    await db.film_projects.update_one({"id": pid}, {"$set": {"pipeline_timers.hype_end": just_past}})
    
    # Spam complete-hype while timer just expired (race condition test)
    tasks = [api_post(session, token, f"/films/{pid}/complete-hype") for _ in range(5)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    _, d2 = await api_get(session, token, f"/films/{pid}")
    state = d2["film"]["pipeline_state"]
    log("Timer edge: una sola transizione", state == "casting_live", f"state={state}")
    log("Timer edge: non bloccato", d2["film"]["pipeline_locked"] == False, str(d2["film"]["pipeline_locked"]))
    
    await cleanup(db, pid)


# ═══════════════════════════════════════════════════════════════
#  TEST 5: LOCK STALE SIMULATO
# ═══════════════════════════════════════════════════════════════
async def test_stale_lock(session, token, db):
    print("\n═══ TEST 5: LOCK STALE SIMULATO ═══")
    pid = await create_test_film(session, token, "Chaos Lock Test")
    await api_post(session, token, f"/films/{pid}/propose")
    
    # Manually set lock + old timestamp (simulating crash mid-transition)
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    await db.film_projects.update_one({"id": pid}, {"$set": {
        "pipeline_locked": True,
        "pipeline_updated_at": old_time,
    }})
    
    # Try to advance — should auto-recover stale lock
    s, d = await api_post(session, token, f"/films/{pid}/setup-hype", {"duration_hours": 2, "strategy": "sprint"})
    log("Stale lock: auto-recovery funziona", s == 200, f"status={s}")
    
    _, d2 = await api_get(session, token, f"/films/{pid}")
    log("Stale lock: stato avanzato", d2["film"]["pipeline_state"] == "hype_setup", d2["film"]["pipeline_state"])
    log("Stale lock: lock rilasciato", d2["film"]["pipeline_locked"] == False, str(d2["film"]["pipeline_locked"]))
    
    # Test fresh lock (< 30s) should block
    await db.film_projects.update_one({"id": pid}, {"$set": {
        "pipeline_locked": True,
        "pipeline_updated_at": datetime.now(timezone.utc).isoformat(),
    }})
    s2, d3 = await api_post(session, token, f"/films/{pid}/launch-hype")
    log("Fresh lock: blocca correttamente", s2 == 423, f"status={s2}")
    
    # Cleanup lock for next tests
    await db.film_projects.update_one({"id": pid}, {"$set": {"pipeline_locked": False}})
    await cleanup(db, pid)


# ═══════════════════════════════════════════════════════════════
#  TEST 6: RETE INSTABILE (retry sicuro grazie a idempotenza)
# ═══════════════════════════════════════════════════════════════
async def test_network_retry(session, token, db):
    print("\n═══ TEST 6: RETE INSTABILE (retry idempotente) ═══")
    pid = await create_test_film(session, token, "Chaos Network Test")
    
    # Simulate: user calls propose, doesn't get response, retries
    s1, d1 = await api_post(session, token, f"/films/{pid}/propose")
    log("Retry 1: propose OK", s1 == 200)
    
    # "Retry" — same call again
    s2, d2 = await api_post(session, token, f"/films/{pid}/propose")
    log("Retry 2: propose idempotente", s2 == 200, d2.get("message", ""))
    
    # Triple retry
    s3, d3 = await api_post(session, token, f"/films/{pid}/propose")
    log("Retry 3: propose ancora OK", s3 == 200)
    
    # State should be exactly proposed (not advanced further)
    _, d4 = await api_get(session, token, f"/films/{pid}")
    log("Retry: stato coerente", d4["film"]["pipeline_state"] == "proposed", d4["film"]["pipeline_state"])
    
    # Advance and retry complete flow
    await api_post(session, token, f"/films/{pid}/setup-hype", {"duration_hours": 2, "strategy": "sprint"})
    await api_post(session, token, f"/films/{pid}/setup-hype", {"duration_hours": 4, "strategy": "bilanciata"})  # retry with diff params
    _, d5 = await api_get(session, token, f"/films/{pid}")
    log("Retry setup-hype: no doppio avanzamento", d5["film"]["pipeline_state"] == "hype_setup", d5["film"]["pipeline_state"])
    
    await cleanup(db, pid)


# ═══════════════════════════════════════════════════════════════
#  TEST 7: MULTI-TAB (2 sessioni contemporanee)
# ═══════════════════════════════════════════════════════════════
async def test_multi_tab(session, token, db):
    print("\n═══ TEST 7: MULTI-TAB ═══")
    pid = await create_test_film(session, token, "Chaos MultiTab Test")
    
    # Get second token (same user, simulating 2 tabs)
    async with aiohttp.ClientSession() as session2:
        token2 = await login(session2)
        
        # Both tabs try to propose at the same time
        t1 = api_post(session, token, f"/films/{pid}/propose")
        t2 = api_post(session2, token2, f"/films/{pid}/propose")
        r1, r2 = await asyncio.gather(t1, t2, return_exceptions=True)
        
        _, d = await api_get(session, token, f"/films/{pid}")
        state = d["film"]["pipeline_state"]
        log("Multi-tab propose: stato coerente", state == "proposed", f"state={state}")
        log("Multi-tab propose: no corruzione", d["film"]["pipeline_locked"] == False)
        
        # Both tabs try setup-hype simultaneously with different strategies
        t3 = api_post(session, token, f"/films/{pid}/setup-hype", {"duration_hours": 2, "strategy": "sprint"})
        t4 = api_post(session2, token2, f"/films/{pid}/setup-hype", {"duration_hours": 10, "strategy": "costruzione_lenta"})
        r3, r4 = await asyncio.gather(t3, t4, return_exceptions=True)
        
        _, d2 = await api_get(session, token, f"/films/{pid}")
        state2 = d2["film"]["pipeline_state"]
        log("Multi-tab setup-hype: stato coerente", state2 == "hype_setup", f"state={state2}")
        log("Multi-tab: pipeline non corrotta", d2["film"]["pipeline_locked"] == False)
        
        # Both tabs launch hype
        t5 = api_post(session, token, f"/films/{pid}/launch-hype")
        t6 = api_post(session2, token2, f"/films/{pid}/launch-hype")
        r5, r6 = await asyncio.gather(t5, t6, return_exceptions=True)
        
        _, d3 = await api_get(session, token, f"/films/{pid}")
        state3 = d3["film"]["pipeline_state"]
        log("Multi-tab launch: stato coerente", state3 == "hype_live", f"state={state3}")
        log("Multi-tab: proposals presenti", len(d3["film"].get("cast_proposals", [])) > 0, str(len(d3["film"].get("cast_proposals", []))))
    
    await cleanup(db, pid)


async def cleanup(db, pid):
    await db.film_projects.delete_many({"id": pid, "pipeline_version": 2})
    await db.films.delete_many({"pipeline_project_id": pid})


async def main():
    print("=" * 60)
    print("  CHAOS TEST — Pipeline V2 Simulazione Utente Caotico")
    print("=" * 60)
    
    client = AsyncIOMotorClient(MONGO)
    db = client["cineworld"]
    
    async with aiohttp.ClientSession() as session:
        token = await login(session)
        print(f"Login OK")
        
        await test_spam_click(session, token, db)
        await test_refresh(session, token, db)
        await test_navigation(session, token, db)
        await test_timer_edge(session, token, db)
        await test_stale_lock(session, token, db)
        await test_network_retry(session, token, db)
        await test_multi_tab(session, token, db)
    
    print("\n" + "=" * 60)
    print(f"  RISULTATO: {results['pass']} PASS / {results['fail']} FAIL")
    print("=" * 60)
    for d in results["details"]:
        print(f"  {d}")
    
    if results["fail"] > 0:
        print(f"\n  ⚠ {results['fail']} TEST FALLITI")
        sys.exit(1)
    else:
        print(f"\n  ✓ TUTTI I {results['pass']} TEST PASSATI — PIPELINE INATTACCABILE")
        sys.exit(0)

asyncio.run(main())
