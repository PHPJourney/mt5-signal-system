# TradeMind MT5 - Quick Reference Card

## 🚀 Quick Start (3 Steps)

```
1. Double-click: deploy.bat
2. Configure in GUI panel
3. Start servers: start_master.bat + start_slave.bat
```

---

## 📂 Key Files

| File | Purpose |
|------|---------|
| `deploy.bat` | One-click deployment |
| `config_panel.bat` | Configuration GUI |
| `start_master.bat` | Start master server |
| `start_slave.bat` | Start slave server |
| `config/slave_config.json` | Main config file |

---

## ⚙️ Common Configurations

### Standard Copy (1x)
```json
"multiplier": 1.0
"reverse_trading": false
```

### Half Position
```json
"multiplier": 0.5
"max_lot_size": 5.0
```

### Reverse Trading
```json
"multiplier": 1.0
"reverse_trading": true
```

### Symbol Mapping
```json
"symbol_mapping": {
    "XAUUSD": "GOLD",
    "BTCUSD": "BITCOIN"
}
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Python not found | Install Python 3.7+, check "Add to PATH" |
| MQTT connection failed | Run: `net start mosquitto` |
| MT5 init failed | Login to MT5 terminal first |
| Symbol not mapped | Add mapping in config panel |
| Order not executed | Check logs/risk_manager.log |

---

## 📊 Log Files

- `logs/master.log` - Master server logs
- `logs/slave.log` - Slave server logs
- `logs/risk_manager.log` - Risk control logs
- `logs/symbol_mapper.log` - Symbol mapping logs

---

## 🎯 Key Features

✅ Real-time signal transmission (MQTT)
✅ Flexible copy multiplier (0.1x - any)
✅ Reverse trading support
✅ Complete symbol mapping
✅ Risk management (daily loss, spread filter, lot limits)
✅ GUI configuration panel
✅ One-click Windows deployment

---

## 💡 Tips

1. **Test first**: Use demo account for 1-2 weeks
2. **Enable risk management**: Always set daily loss limit
3. **Monitor logs**: Check logs/ directory regularly
4. **Backup configs**: Save config files periodically
5. **Start small**: Begin with low multiplier in live trading

---

## 📞 Support

- Read: WINDOWS_GUIDE.md (detailed guide)
- Read: README.md (complete manual)
- Test: `python test/test_mqtt.py`
- Check: logs/ directory for errors

---

**Version**: 1.0.0 | **Date**: 2026-04-15
