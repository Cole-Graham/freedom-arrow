# Freedom Arrow 0.1 deployment candidate

**Use 0.1.1 for the Linux startup/scoring compatibility fix and the T-90M armor correction. Detection, stealth and concealment remain vanilla. Custom scoring requires guarded offline Local AI Skirmish; full balance acceptance is still incomplete.**

- [Linux installation and rollback](../../docs/releases/0.1-linux.md)
- [Package](FreedomArrow-0.1.1.bamod) and [checksum](SHA256SUMS.txt)
- [Exact scope and verification limits](EVIDENCE.md)
- [Offline archive verification](verify.py)

This directory freezes the tested application-host source, checksum-pinned input
configuration and edited constants used for this candidate. It contains no game
DLL, complete vanilla table dump, game bundle or filled-in developer config.
The branch is for review; it does not replace the repository's main pipeline or
make the default `python -m pipeline package` emit this multi-DLL candidate.
Use this directory's artifact or build command for this version.

Build from source after MelonLoader has generated the assemblies for the pinned
compatible game installation (requires Python 3 and the .NET 6/8 SDK):

```bash
python3 releases/0.1/build.py --game-dir "/path/to/Broken Arrow"
python3 releases/0.1/verify.py releases/0.1/out/FreedomArrow-0.1.1.bamod
```

The build writes only this checkout's ignored `out/` and project build folders.
It does not install or launch the game. Output hashes are generated for the rebuilt
DLLs; byte-for-byte reproduction of the prepared artifact is not asserted.

The ordinary repository formula-host integration and final online/multiplayer
support remain separate review work. Do not combine the included Runtime host
with another FreedomArrow/ActualArrow package that edits the same paths.

0.1.0 is retained as the historical artifact and is superseded for deployment.
Run the independent metadata regression checks without a game:

```bash
dotnet run --project releases/0.1/fingerprint-tests/Tests.csproj -c Release
```
