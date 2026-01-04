<div align="center">
  <img src="icon.png" width="100px" alt="Local DataLab" />
  <h1>Local Data Lab</h1>

  <p>Local Data Lab is a containerized, local-first data platform based on Airflow and Localstack (AWS) on Minikube (k8) with IaC using Terraform.</p>

  <p>
    <img src="https://img.shields.io/static/v1?label=VS+Code&message=DevContainer&logo=visualstudiocode&color=007ACC&logoColor=007ACC&labelColor=2C2C32" alt="DevContainer">
    <img src="https://img.shields.io/badge/Apache%20Airflow-017CEE?logo=apacheairflow&logoColor=fff" alt="Airflow">
    <img src="https://img.shields.io/badge/LocalStack-23B0A6?logo=localstack&logoColor=white" alt="LocalStack">
    <img src="https://img.shields.io/badge/Minikube-2B6CB0?logo=minikube&logoColor=white" alt="Minikube">
    <img src="https://img.shields.io/badge/Kubernetes-326CE5?&style=plastic&logo=kubernetes&logoColor=white" alt="Kubernetes">
    <img src="https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white" alt="Terraform">
    <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker">
  </p>
  <a href="https://github.com/nitish-raj/local-datalab/actions/workflows/terraform-validate.yaml">
    <img src="https://github.com/nitish-raj/local-datalab/actions/workflows/terraform-validate.yaml/badge.svg" alt="terraform-validate">
  </a>
  <a href="https://github.com/nitish-raj/local-datalab/actions/workflows/python-test.yaml">
    <img src="https://github.com/nitish-raj/local-datalab/actions/workflows/python-test.yaml/badge.svg" alt="python-test">
  </a>

</div>

> [!NOTE]
> This repo is designed to run with **Dev Containers** only.
> Please ensure all prerequisites are complete for a smooth setup.
> If you don’t use Dev Containers, additional host-specific setup is required (macOS, Linux, or Windows).

## System Requirements
- macOS, Linux, or Windows (with WSL2) capable of running Docker
- 4 CPU cores minimum (8 recommended for smoother Minikube + Localstack)
- 8 GB RAM minimum (16 GB recommended)
- 10+ GB free disk space for images, caches, and Terraform providers
- Hardware virtualization enabled (required by Docker Desktop/WSL2)

## Prerequisites
- `Docker Desktop`
  - Install: https://docs.docker.com/get-docker/
  - Must allow privileged containers and bind-mounting the repo directory
- `VS Code` with the `Dev Containers extension`
- `Git`
- Network access to pull images and features from Docker Hub/GHCR and Terraform providers
- A local `.env` file at repo root
  - Use the existing `.env` as a template and replace values for your environment as needed

## How to Run in Devcontainer
1. Open this repo in `VS Code`
2. Open `Command Pallet` from settings or use shortcut `CTRL/CMD + SHIFT + P`, and run `Dev Containers: Reopen in Container`
3. The container build will run `.devcontainer/bootstrap.sh` on first start; it provisions Minikube, applies Terraform, and starts port forwards. This may take 10-20 minutes depending on system resources and network speed.
4. After the container starts, access services:
   - Airflow UI: http://localhost:8080 (default user: `admin`, password: `admin`)
       - Trigger first DAG with prefix `01_`, it will auto trigger subsequesnt DAGs `02_` and `03_`
   - Localstack: It does not have a UI, but you can interact with it using AWS CLI or SDKs at `http://localhost:4566`. For example, list S3 buckets with:
      ```
      aws --endpoint-url=http://localhost:4566 s3 ls
      ```
   - Minikube Dashboard: Run `minikube dashboard -p local-datalab --url` in the devcontainer terminal to get the URL.


## Architecture Diagram
![Infra Architecture](https://mermaid.ink/svg/pako:eNqlWG1v2zYQ_iuE-qE2RiWSJcu22hVI423NlhZZ3BdgdRHQEmkLlkWDpGKndf_7SL1QlC0HA5ZPIe-ee7_jyT-siMbYCi3btudZRDOSLMN5BgBJ6S5aISaKEwArsUlv0QKnPASC5VjdpuiJ5iIEOF2ro1jhDQ7BAnGsj58RS9AixbwSQ2gmZsl3yeb62_08K9RqXeD2XrHxfLFkaLsCU_woTRIoyTB7S_df59ZrvkUZ4OIpxb--VMJsrqS5wXb_qhBu73CyXIkwcJyXb0w86H2egWvpLPgFTGm0xqz_-lJJezO3vpXGxQnDkUhoVthR3pm23GIipA22BpiQj2_ru4rzKotWlPV6oN8Pw7CMVc3yETOGCGUbKY6gkCBbpaG5Br0kIwxdivqib-i8pRFKp2jJNZjQNJYeTq_-4KB3cYkSpkJqYq4Zzd5RLhp9qYwBUFcFTcJiI1iX_CmL7FjquOCrTt3Att8cFBfgNGcRPmgVJSvO4pMQvk-yZJ0v8HWac-nZM-kcdqazxoNKwHH-jjNY3tWo5_KhTfwwmyKBnrHM77TsA9pgCYgwiCXcTtHi1LbuYqlCygWK1rPHSOcH72VHZEtso1SAGWaPiRSeatbQHwZBS3gj5o7GTZpVuBoSkLRzqM_XX3slaBXHhip7-xj1v9XJbEVr5r3NZScJVYmGkpkHqvuWru70qL97tNMWIxatkkcMGNo9cCRwmiYCPywKeUfi7hiNMOc4PgFva8oDokk3WBVxaeUJuuqfB1X_XWCjtk8SWPTF1Rc5am5vwKUKxdXdzaGdnTNJU9AmpM8wHeRB4EM7eTV_yzijrq9Kp_5HaVdh-e-VXal8h9NNuyArAlAUcI9TrJ4MU97VNlE1X8yIEseLowomKCmgV9kD0DapyP2WkFm0wnGeGkJkuGR4ECubqia3QLIsqrKiDY4kadmIkgo0uYX7Qtna1ETliCzvQO8v6TPLsMD8tz2OckGPDP3IkuUSMwO-oFKZvm4x38kRu2SY182qBo56cmvC7O_bftsfftTaVdyK8Q4krX8aeDlsnp9EtYwm9uHYGTvHoeTqUTh6c9TVn3TRMsNWL0kB7qyeojN0TZxnaVJ6lsXM73muMnPn6U1qzrLUeWq5VLtgOiTDeY6jSl5HSXeTTee6OaqS7KRpp7rJHZEs0tsaPOeefrkT3auZ8t_Wp4L1uff6jjLxO2U7xJrZz1AW001BklOsoIHjoqx8-HSjUcuUGgPp043BbCgp81WDDTdP9r2Cs71ylFztuzKCLU_rmDVLoBr1zewAspiKVYsfjjepEtjUU1WA2nxF11lpHr7yLfGAar5DK5_1_wXHjskXmB_Miqh3vVMJpeRSU5QizqeYgGKZBXKKpuELjElACOSC0TUOX3iL8YAEMKIpZeELh7ijAXrVAtdjvoSTERka8FHkIRzXcJe4rj9qw5tFpjaAECQ11hJcZzEZu9qAobc4NiDJZIgzlIISIgcWlx8rDD2FwAcerOxySEz8RmqAPB81UgfYDdpS1dw2_SJkJB2p8WQy8lwdFt9zfefIrzypkTEZkLFG4sgfTyYaiRzfx0cRKVqpRAvZNfI5ZzgTtQTzqpRi3BSS0iRbz9T6ANwxdCegA1iFapfEYhU6232nJG1VU_PwqLLh0SdgWUqNP-ZUgnp4Qj0noTkSYTn9oB50sB7SsOkdWJU51D1QFaChVC9pujYMYmsdhK3lDbY2NijXXqh3WGj0ZVOzhlyjn6EeRbIMDJa6LWHzmVaX2SsLWkuWxJYceinH0NpgtkHqbP1QAuZW8b0-t0L5b4wJylO59M6znxIn171_KN1Yofrwhxaj-XKl5eRbqQJPEyQHfcMipw1m1zTPhBW6g0KEFf6w9lZoB8HowvEHo6HnjQeu43jQerLCcXAxkBXvjf3hxJO0wU9ofS-Uuhf-0BkEQzeYuL4XjIIxtHCcyC3qffnTRfELxs9_AYUUgoM)

## Data Flow Diagram (DAGs + Pipeline)
![DAG Architecture](https://mermaid.ink/svg/pako:eNp9Vm1v2zYQ_isE82VDZccSFTtRX4CsxoYC2TokQT9sHgRaImUuFOmRVJ00zn_fkXqJ7DQFDJoU77l77vicqEdc6JLhDE8mk5UqtOKiylYKIS71rthQ48IKoY2r5RVdM2kz5EzD_FNJH3TjMsTknV-6DatZhtbUsmH5hRpB15LZzg3Xyt2Ib2AWp9v7lQphh1jo6tqb2WZdGbrdoKWgMKl_0fd_r_Dy8je0pI6iX8F8hf9pHQ62NwRsrnRBpXW0uIP1YIPQNd3BrqG73FLHpBSO5eumuGPu3dqcfuCCydKetn_Tiul_rVYj-J9GF8xaVoKTbT_PqRadk8GUqXKljogB71nc8Z_FGbKibiSwCHhudJ23cUfxlrP41kPWjZAQR5V5s5WaloGsUJwZdPn5k0VvkKMVOoK_xiHpOSQZEqpi1uWWKScUk0leQmEPCCSBQMVc7kVxtJUM3Er6YAOrWqiftpJ6f5X3xn5GTsMPDI7A_pza-AF4c3v5EVlGTbFB2zax05egGE0mH9rYw4z8OF_S50syBKoo2qKXVMiHXJVfxUEE8nq6ZJSuP7KdNneB-UG66N17ZBqVH1MnId9C19umO3IfO-CDTv0A51hTewd_fyy_fDqCpwDfGTFQh44DV_aYfVcVMtQHAg-z9EWloCH87r7UO-WVhQ61v28l2NqGabAOPFDJjPjKylNIxk69NRDvn7Vu8p1wG5_ss7-hhY593hpRVcwsaXXdqM-gAOq02beK7dkO4IAwDPiOg78aNOilD9hJZx9OSwoLL67-BAep7sfCCtMA-a9h5gEFpb4BrUpWOASVqO0r9m2dbJIbxjuWnbTDPwTqOtl3ga9jLsr30-n01HPzk-_Uq_f93Xr1btu6kR_UbUxq38qkj9ApprMTlQJcyJmCC2dfWKejXPsGE1qFfJyomQVNMNtnfpTSoMVCgvsl48gSOEgpsxPG-JzzyDqj71h2QtbnCZ9HhZbaZCczHi8S-vYAWYaXoIfyBT8bQRcFoazsoTGP43RxCHW-7zos5wsw7rH8YkHiIWxK4nR2hF3r-2coH4W9SCmQ7paTnSjdJou396-lMLrmvM_RBnRp9HyGlowx_laJQpeEkfgqjPd9g0Xh1RnGJIwkCi-LMCZhbJ-koRBvcYQrI0qccbhFWYRrZmrq1_jRe17hcKevcAbTknHaSLj6VuoJcFuq_tK6xpn_OIiw0U21Gfw0Wy_sLs3BBCTAzEfdKIezi-ABZ4_4HmeT-XwxnaXJ4oyQ8ySezUiEH3B2Pp8mcCTkPD27ILCXPEX4W4gZT9OzWTI_i-cXcUrmi_l5hFkpoDF-b79uwkfO0_-3adXl)


### DAG Workflow Summary
- **DAG 01** infers AOIs from field polygons, tags each field with an `aoi_id`, writes outputs under `derived/` (`aois.json`, `fields_with_aoi.geojson`), then triggers DAG 02.
- **DAG 02** builds a daily date range from the **earliest planting date to today**, runs a STAC search per **AOI × day**, writes results under `ingest/` (`ingest/aoi_id=.../date=.../s2_refs.json`), and triggers DAG 03 **for each day**.
- **DAG 03** filters fields by `planting_date ≤ run_day`, unions eligible fields by AOI, computes NDVI per AOI using the day’s ref, and writes outputs under `calculation/` (`calculation/aoi_timeseries/...`).


## Sample GeoJSON Input
```geojson
{
    "type": "FeatureCollection",
    "name": "fields_with_planting_dates",
    "crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    },
    "features": [
        {
            "type": "Feature",
            "properties": {
                "field_id": "F001",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            5.981582361085373,
                            49.843839468148417
                        ],
                        [
                            6.045924169409432,
                            49.814862290427499
                        ],
                        [
                            6.137394643323546,
                            49.792618642440431
                        ],
                        [
                            6.149838830646104,
                            49.839550641591671
                        ],
                        [
                            6.067066789048511,
                            49.922667846443062
                        ],
                        [
                            6.029908833583306,
                            49.919623777909635
                        ],
                        [
                            5.994228367256596,
                            49.914452910345943
                        ],
                        [
                            5.981582361085373,
                            49.843839468148417
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F002",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            5.904589611221184,
                            50.084859010228996
                        ],
                        [
                            5.91742516073225,
                            49.979042851312187
                        ],
                        [
                            6.077849604023584,
                            50.014934898401009
                        ],
                        [
                            6.086947137891542,
                            50.088224378634209
                        ],
                        [
                            5.904589611221184,
                            50.084859010228996
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F003",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            5.00572716705895,
                            50.332855540147108
                        ],
                        [
                            4.980389969145307,
                            50.271442444152257
                        ],
                        [
                            5.053011906393778,
                            50.186334226955637
                        ],
                        [
                            5.125889921160194,
                            50.233988582259315
                        ],
                        [
                            5.125931960969154,
                            50.295444814398877
                        ],
                        [
                            5.00572716705895,
                            50.332855540147108
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F004",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            7.505518494300873,
                            51.157409464436
                        ],
                        [
                            7.451011029000597,
                            51.079936985529002
                        ],
                        [
                            7.592357102499221,
                            51.018162876287647
                        ],
                        [
                            7.655415304927146,
                            51.119734472402712
                        ],
                        [
                            7.505518494300873,
                            51.157409464436
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F005",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            7.549310877193335,
                            50.272204021063146
                        ],
                        [
                            7.619307990307675,
                            50.118921673410256
                        ],
                        [
                            7.769167731126856,
                            50.172080134086372
                        ],
                        [
                            7.733706828642255,
                            50.288111090814795
                        ],
                        [
                            7.549310877193335,
                            50.272204021063146
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F006",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            6.321730870183046,
                            49.783697702623897
                        ],
                        [
                            6.326552331751657,
                            49.713477848709545
                        ],
                        [
                            6.434076270698228,
                            49.745743310539979
                        ],
                        [
                            6.43354447246449,
                            49.790010160184778
                        ],
                        [
                            6.321730870183046,
                            49.783697702623897
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F007",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            5.978062868139205,
                            49.69562786064796
                        ],
                        [
                            5.960079815419874,
                            49.658537379869102
                        ],
                        [
                            5.966954464925919,
                            49.626095012992948
                        ],
                        [
                            6.071525149114848,
                            49.639531655268456
                        ],
                        [
                            6.113675321822541,
                            49.681367382927789
                        ],
                        [
                            5.978062868139205,
                            49.69562786064796
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F008",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            6.962617377567369,
                            49.813013987023112
                        ],
                        [
                            6.990912300739609,
                            49.747764615669666
                        ],
                        [
                            7.131869516480037,
                            49.738156870033748
                        ],
                        [
                            7.195797828458382,
                            49.811105256751006
                        ],
                        [
                            6.962617377567369,
                            49.813013987023112
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F009",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            7.688218168752599,
                            51.167190539851134
                        ],
                        [
                            7.708766350329483,
                            51.120220425523172
                        ],
                        [
                            7.777870150899332,
                            51.126085245049723
                        ],
                        [
                            7.809781799041673,
                            51.16641132199095
                        ],
                        [
                            7.688218168752599,
                            51.167190539851134
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F010",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            7.714060584180601,
                            51.092790481677071
                        ],
                        [
                            7.656493647408183,
                            51.036049713578564
                        ],
                        [
                            7.745864278056956,
                            51.025978231929514
                        ],
                        [
                            7.801603964416472,
                            51.09087171669961
                        ],
                        [
                            7.714060584180601,
                            51.092790481677071
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F011",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            5.107245152298788,
                            50.185720503725832
                        ],
                        [
                            5.04870023206368,
                            50.136964817740022
                        ],
                        [
                            5.171776333603958,
                            50.142695528438225
                        ],
                        [
                            5.197107211213421,
                            50.19178312730395
                        ],
                        [
                            5.107245152298788,
                            50.185720503725832
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F012",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            7.053736162139813,
                            49.895071118590039
                        ],
                        [
                            6.941655964314606,
                            49.868928808638572
                        ],
                        [
                            6.956797743187224,
                            49.836333528690517
                        ],
                        [
                            7.233986410423455,
                            49.855442340437975
                        ],
                        [
                            7.053736162139813,
                            49.895071118590039
                        ]
                    ]
                ]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "field_id": "F013",
                "planting_date": "2026-01-01"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [
                            7.757737684006969,
                            50.290945317290976
                        ],
                        [
                            7.791455749988984,
                            50.177502981726889
                        ],
                        [
                            7.863551107456061,
                            50.202927574258467
                        ],
                        [
                            7.875592852058759,
                            50.293387831374702
                        ],
                        [
                            7.757737684006969,
                            50.290945317290976
                        ]
                    ]
                ]
            }
        }
    ]
}
```
