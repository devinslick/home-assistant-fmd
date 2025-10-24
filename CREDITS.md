# Credits and Attribution

## FMD (Find My Device) Project

This Home Assistant integration is built to work with the **FMD (Find My Device)** open source project, maintained by the FMD-FOSS team.

### FMD Project Links

- **FMD Android App**: https://gitlab.com/fmd-foss/fmd-android
- **FMD Server**: https://gitlab.com/fmd-foss/fmd-server
- **Project Website**: https://fmd-foss.org

### FMD Team

The FMD project was created and is maintained by:

- **Nulide** (Founder) - http://nulide.de
- **Thore** (Maintainer) - https://thore.io

### What is FMD?

FMD (Find My Device) is a free and open source Android app and server that allows you to:
- Track your device location
- Send commands remotely (ring, lock, wipe, etc.)
- Take photos remotely
- Control device settings

The FMD team has created both:
1. **FMD Android App** - Runs on your Android device to respond to commands
2. **FMD Server** - Self-hosted server that stores encrypted location data and relays commands

### This Integration's Role

This Home Assistant custom integration (`home-assistant-fmd`) acts as a **client** for the FMD server:
- Fetches encrypted location data from your FMD server
- Sends commands to your device via the FMD server
- Displays device information in Home Assistant

**Important**: This integration requires you to:
1. Install the FMD Android app on your device
2. Run your own FMD server (or use a hosted instance)
3. Configure the FMD app to connect to your server

This integration does **not** include or redistribute any FMD server or Android app code. It simply communicates with your existing FMD infrastructure using the FMD API.

### Attribution and Respect

We want to give full credit to the FMD team for their excellent work:

- ✅ **FMD created the protocol** - This integration follows their API design
- ✅ **FMD created the encryption** - We use their RSA + AES-GCM encryption scheme
- ✅ **FMD created the server** - We communicate with their server implementation
- ✅ **FMD created the Android app** - We send commands to their app

This integration would not exist without the FMD team's incredible open source work. We are deeply grateful for their efforts in creating a privacy-respecting, self-hosted device tracking solution.

### Supporting the FMD Project

If you find this integration useful, please consider:
- ⭐ Starring the FMD repositories on GitLab
- 📝 Contributing to the FMD project
- 🐛 Reporting bugs to help improve FMD
- 📢 Spreading the word about FMD

### Licensing Compatibility

- **FMD Server**: GNU Affero General Public License v3.0 (AGPL-3.0)
- **FMD Android App**: GNU General Public License v3.0 (GPL-3.0)
- **This Integration**: MIT License

This integration is a separate client that communicates with FMD over the network. It does not incorporate or link with FMD code, so MIT License is appropriate and compatible. We respect and acknowledge the GPL/AGPL licenses of the FMD components.

### Thank You

A huge thank you to **Nulide**, **Thore**, and all FMD contributors for creating and maintaining this fantastic open source project. Your work enables privacy-conscious device tracking for everyone.

---

## This Integration

**Home Assistant FMD Integration**
**Author**: Devin Slick ([@devinslick](https://github.com/devinslick))
**Repository**: https://github.com/devinslick/home-assistant-fmd
**License**: MIT License

### Integration Contributors

We welcome contributions to this Home Assistant integration! See our [LICENSE](LICENSE) file for terms.

### Disclaimer

This integration is not officially affiliated with or endorsed by the FMD-FOSS project. It is an independent third-party client created to integrate FMD with Home Assistant.

If you have questions about:
- **FMD server or Android app** → Contact the FMD team
- **This Home Assistant integration** → Open an issue on this repository
