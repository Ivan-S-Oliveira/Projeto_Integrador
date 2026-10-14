import numpy as np
import pandas as pd


def criar_particoes_agrupadas(
    base: pd.DataFrame,
    grupo: str,
    estrato: str,
    frac_treino: float,
    frac_validacao: float,
    frac_teste: float,
    seed: int,
) -> pd.Series:
    """
    Cria particoes reproduziveis e mantem cada grupo
    integralmente em uma unica particao.
    """
    soma_fracoes = (
        frac_treino
        + frac_validacao
        + frac_teste
    )

    if not np.isclose(
        soma_fracoes,
        1.0,
    ):
        raise ValueError(
            "As fracoes do split precisam somar 1."
        )

    colunas_necessarias = {
        grupo,
        estrato,
    }

    colunas_ausentes = sorted(
        colunas_necessarias
        - set(base.columns)
    )

    if colunas_ausentes:
        raise KeyError(
            "Colunas necessarias ao split ausentes: "
            f"{colunas_ausentes}"
        )

    if base[grupo].isna().any():
        raise ValueError(
            f"A coluna de grupo {grupo!r} "
            "contem valores ausentes."
        )

    if base[estrato].isna().any():
        raise ValueError(
            f"A coluna de estrato {estrato!r} "
            "contem valores ausentes."
        )

    mascara_grupos_repetidos = (
        base[grupo].duplicated(
            keep=False
        )
    )

    if mascara_grupos_repetidos.any():
        estratos_por_grupo_repetido = (
            base.loc[
                mascara_grupos_repetidos,
                [
                    grupo,
                    estrato,
                ],
            ]
            .groupby(
                grupo,
                sort=False,
                observed=True,
            )[estrato]
            .nunique(
                dropna=False
            )
        )

        grupos_conflitantes = (
            estratos_por_grupo_repetido.loc[
                estratos_por_grupo_repetido.gt(1)
            ]
        )

        if not grupos_conflitantes.empty:
            exemplos = (
                grupos_conflitantes
                .head(10)
                .index
                .astype(str)
                .tolist()
            )

            raise ValueError(
                "Foram encontrados identificadores "
                "associados a mais de um estrato. "
                f"Exemplos: {exemplos}"
            )

    resumo_grupos = (
        base.loc[
            :,
            [
                grupo,
                estrato,
            ],
        ]
        .drop_duplicates(
            subset=grupo,
            keep="first",
        )
        .reset_index(
            drop=True
        )
    )

    quantidade_grupos = len(
        resumo_grupos
    )

    if quantidade_grupos == 0:
        raise ValueError(
            "Nenhum grupo disponivel para "
            "criar as particoes."
        )

    particoes_grupos = np.empty(
        quantidade_grupos,
        dtype=object,
    )

    particoes_grupos[:] = None

    rng = np.random.default_rng(
        seed
    )

    indices_por_estrato = (
        resumo_grupos.groupby(
            estrato,
            sort=False,
            observed=True,
        )
        .indices
    )

    for indices_bloco in (
        indices_por_estrato.values()
    ):
        indices = np.asarray(
            indices_bloco,
            dtype=np.int64,
        )

        indices = rng.permutation(
            indices
        )

        quantidade = len(
            indices
        )

        if quantidade == 0:
            continue

        quantidade_treino = int(
            np.floor(
                quantidade
                * frac_treino
            )
        )

        quantidade_validacao = int(
            np.floor(
                quantidade
                * frac_validacao
            )
        )

        if quantidade >= 3:
            quantidade_treino = max(
                quantidade_treino,
                1,
            )

            quantidade_validacao = max(
                quantidade_validacao,
                1,
            )

            quantidade_teste = (
                quantidade
                - quantidade_treino
                - quantidade_validacao
            )

            if quantidade_teste < 1:
                excesso = (
                    1
                    - quantidade_teste
                )

                reducao_treino = min(
                    excesso,
                    max(
                        quantidade_treino - 1,
                        0,
                    ),
                )

                quantidade_treino -= (
                    reducao_treino
                )

                excesso -= reducao_treino

                if excesso > 0:
                    quantidade_validacao -= (
                        excesso
                    )

        fim_treino = (
            quantidade_treino
        )

        fim_validacao = (
            quantidade_treino
            + quantidade_validacao
        )

        particoes_grupos[
            indices[:fim_treino]
        ] = "treino"

        particoes_grupos[
            indices[
                fim_treino:fim_validacao
            ]
        ] = "validacao"

        particoes_grupos[
            indices[fim_validacao:]
        ] = "teste"

    resumo_grupos["particao"] = pd.Series(
        particoes_grupos,
        index=resumo_grupos.index,
        dtype="string",
    )

    if resumo_grupos[
        "particao"
    ].isna().any():
        quantidade_sem_particao = int(
            resumo_grupos[
                "particao"
            ].isna().sum()
        )

        raise RuntimeError(
            "Existem grupos sem particao "
            "apos o split: "
            f"{quantidade_sem_particao}"
        )

    mapa_particoes = (
        resumo_grupos
        .set_index(
            grupo
        )["particao"]
    )

    particao = (
        base[grupo]
        .map(
            mapa_particoes
        )
        .astype(
            "string"
        )
    )

    if particao.isna().any():
        quantidade_sem_particao = int(
            particao.isna().sum()
        )

        raise RuntimeError(
            "Existem linhas sem particao depois "
            "do mapeamento por grupo: "
            f"{quantidade_sem_particao}"
        )

    return particao