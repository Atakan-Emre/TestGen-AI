# Repo Sample Outputs

Bu klasor, runtime'da uretilen gecici ciktidan farkli olarak repoda bilerek tutulan ornek output setidir.

Kaynak girdiler:

- `data/input/Csv/example.csv`
- `data/input/Json/Example-Header.json`
- `data/input/Variables/variablesHeader.txt`

Icerik:

- `scenarios/test.txt`
- `scenarios/test.meta.json`
- `test_cases/bsc/bsc_test.json`
- `test_cases/ngi/ngi_test.json`
- `test_cases/opt/opt_test.json`

Gercek uretim sonucu:

- `BSC: 1`
- `NGI: 21`
- `NGV: 0`
- `OPT: 4`
- `Toplam: 26`

Not:

- Bu ornek veri setinde `NGV` route'u basarili donse de dosya uretmedi, bu yuzden repoda sabit `NGV` sample dosyasi tutulmuyor.

Amac:

- repo klonlandiginda sadece input degil output ornegi de gorunsun
- README'de anlatilan akisin somut sonucu repoda bulunsun
- runtime `data/output` klasoru temiz tutulurken, sabit sample set korunabilsin
