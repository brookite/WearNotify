def send(ctx, packet):
    try:
        import androidhelper
        droid = androidhelper.Android()
        droid.notify("s", packet)
    except Exception:
        try:
            import plyer
            plyer.notificaton.notify(title="s", message=packet)
        except Exception:
            print(packet)
            print("=" * 8)
