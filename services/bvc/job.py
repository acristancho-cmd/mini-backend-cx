"""
Job diario BVC: obtiene data de la API y guarda en Supabase.
"""
from datetime import date, datetime, timezone


def run_bvc_fetch_and_save():
    from services.bvc.api import BVCApi
    from services.bvc.cache import save_bvc_day

    trade_date = date.today().isoformat()
    print("[bvc_job] INICIO trade_date=%s (hora UTC %s)" % (trade_date, datetime.now(timezone.utc).isoformat()))

    api = BVCApi()

    local = api.get_mercado_local(fecha=trade_date)
    if local is not None:
        ok = save_bvc_day(trade_date, "mercado_local", local)
        print("[bvc_job] mercado_local: datos=%s, guardado=%s" % (len(local), ok))
    else:
        print("[bvc_job] mercado_local: NO obtenido para %s (API devolvió None)" % trade_date)

    global_data = api.get_mercado_global(fecha=trade_date)
    if global_data is not None:
        ok = save_bvc_day(trade_date, "mercado_global", global_data)
        print("[bvc_job] mercado_global: datos=%s, guardado=%s" % (len(global_data), ok))
    else:
        print("[bvc_job] mercado_global: NO obtenido para %s (API devolvió None)" % trade_date)

    print("[bvc_job] FIN")


def run_bvc_cleanup(days: int = 7):
    from services.bvc.cache import cleanup_older_than
    cleanup_older_than(days=days)
