# Dados da colônia: 31 dias

Dados simulados da Missão Aurora Siger. Energia em kWh por dia, vento em m/s, tempo de sol em horas.

| Dia | Energia total (kWh) | Consumo total (kWh) | Produção total (kWh) | Produção solar (kWh) | Produção eólica (kWh) | Consumo suporte à vida (kWh) | Vento (m/s) | Tempo de sol (h) | Armazenamento (kWh) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 1148 | 700 | 848 | 128 | 720 | 289 | 13.0 | 9.6 | 448 |
| 2 | 1317 | 713 | 869 | 149 | 720 | 319 | 14.1 | 11.2 | 600 |
| 3 | 1364 | 731 | 764 | 128 | 636 | 286 | 10.6 | 9.6 | 600 |
| 4 | 1111 | 756 | 511 | 133 | 378 | 307 | 6.3 | 10.0 | 355 |
| 5 | 1006 | 700 | 651 | 147 | 504 | 315 | 8.4 | 11.0 | 306 |
| 6 | 1175 | 695 | 869 | 149 | 720 | 292 | 14.9 | 11.2 | 480 |
| 7 | 1338 | 676 | 857 | 137 | 720 | 280 | 16.5 | 10.3 | 600 |
| 8 | 1467 | 787 | 867 | 147 | 720 | 315 | 15.3 | 11.0 | 600 |
| 9 | 1473 | 744 | 873 | 159 | 714 | 294 | 11.9 | 11.9 | 600 |
| 10 | 1467 | 770 | 867 | 147 | 720 | 317 | 15.1 | 11.0 | 600 |
| 11 | 1448 | 706 | 848 | 128 | 720 | 287 | 13.8 | 9.6 | 600 |
| 12 | 1149 | 698 | 549 | 135 | 414 | 281 | 6.9 | 10.1 | 451 |
| 13 | 509 | 785 | 59 | 59 | 0 | 289 | 27.1 | 4.4 | 0 |
| 14 | 73 | 714 | 73 | 73 | 0 | 284 | 26.5 | 5.5 | 0 |
| 15 | 868 | 769 | 868 | 148 | 720 | 303 | 16.9 | 11.1 | 99 |
| 16 | 971 | 675 | 872 | 152 | 720 | 287 | 15.3 | 11.4 | 296 |
| 17 | 1002 | 783 | 706 | 136 | 570 | 286 | 9.5 | 10.2 | 219 |
| 18 | 1076 | 738 | 857 | 137 | 720 | 307 | 15.6 | 10.3 | 338 |
| 19 | 1200 | 703 | 861 | 141 | 720 | 289 | 16.1 | 10.6 | 497 |
| 20 | 1353 | 796 | 856 | 136 | 720 | 304 | 12.2 | 10.2 | 557 |
| 21 | 1314 | 769 | 757 | 133 | 624 | 324 | 10.4 | 10.0 | 545 |
| 22 | 1093 | 740 | 548 | 128 | 420 | 281 | 7.0 | 9.6 | 353 |
| 23 | 1214 | 709 | 861 | 141 | 720 | 279 | 14.7 | 10.6 | 505 |
| 24 | 1369 | 810 | 864 | 144 | 720 | 323 | 17.0 | 10.8 | 559 |
| 25 | 1076 | 757 | 517 | 151 | 366 | 309 | 6.1 | 11.3 | 319 |
| 26 | 1001 | 717 | 682 | 148 | 534 | 281 | 8.9 | 11.1 | 284 |
| 27 | 1163 | 734 | 879 | 159 | 720 | 318 | 24.0 | 11.9 | 429 |
| 28 | 1251 | 808 | 822 | 132 | 690 | 320 | 11.5 | 9.9 | 443 |
| 29 | 1149 | 707 | 706 | 148 | 558 | 305 | 9.3 | 11.1 | 442 |
| 30 | 1306 | 761 | 864 | 144 | 720 | 313 | 14.4 | 10.8 | 545 |
| 31 | 1042 | 772 | 497 | 137 | 360 | 277 | 6.0 | 10.3 | 270 |

## valores calculados

- **Produção solar:** 160 kWh em um dia de 12 h de sol (parábola de 20 kW de pico do `funcao_math.md`), proporcional ao tempo de sol.
- **Produção eólica:** 2,5 kW por m/s de vento (reta da regressão), limitada a 30 kW, durante 24 h. Com vento acima de 25 m/s (tempestade) as turbinas desligam e a produção é zero.
- **Produção total:** solar + eólica.
- **Consumo total:** suporte à vida + base (6 kW o tempo todo) + operações (logística e laboratório).
- **Energia total:** energia disponível no dia, ou seja, armazenamento do dia anterior + produção do dia.
- **Armazenamento:** energia total − consumo total, entre 0 e 600 kWh (capacidade da bateria). Começa o dia 1 com 300 kWh.
