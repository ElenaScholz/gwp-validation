import pandas as pd

def merge_hylak_glakes_strict(
    gwp_lakes: pd.DataFrame,
    glakes_hylak: pd.DataFrame,
    hylak_key: str = 'Hylak_id',
    glakes_key: str = 'GLAKES_id',
    how: str = 'inner',
    verbose: bool = True
) -> pd.DataFrame:
    """
    Merge two DataFrames on a Hylak ID while ensuring only clean 1:1 or 1:many relationships are retained.

    This function enforces the following rules:
    1. Keep rows where the Hylak ID appears exactly once in both datasets (1:1 match).
    2. Keep rows where one glakes_id corresponds to multiple Hylak IDs (1:many).
    3. Remove any Hylak IDs that map to more than one glakes_id (many-to-one or many-to-many).
    4. Perform a merge (default: inner) using the cleaned subsets.

    Parameters
    ----------
    gwp_lakes : pd.DataFrame
        DataFrame containing the GWP lakes data with a Hylak ID column.
    glakes_hylak : pd.DataFrame
        DataFrame mapping Hylak IDs to glakes IDs.
    hylak_key : str, optional
        Name of the Hylak ID column used for merging (default: 'Hylak_id').
    glakes_key : str, optional
        Name of the glakes ID column used to detect one-to-many relationships (default: 'glakes_id').
    how : str, optional
        Type of merge to perform ('inner', 'left', 'right', 'outer'). Default is 'inner'.
    verbose : bool, optional
        If True, prints summary statistics for each filtering step (default: True).

    Returns
    -------
    pd.DataFrame
        Merged DataFrame containing only rows that satisfy the 1:1 or valid 1:many criteria.
    np.ndarray
        Array of unique Hylak IDs present in the merged DataFrame - those can be used to filter Li data.
    """

    if verbose:
        print(f"🔹 Starting merge process...")
        print(f"  - GWP lakes: {len(gwp_lakes):,} rows")
        print(f"  - GLAKES-Hylak mapping: {len(glakes_hylak):,} rows")

    # --- Step 1: Count occurrences of Hylak IDs in each dataset
    hylak_counts_gwp = gwp_lakes[hylak_key].value_counts()
    hylak_counts_glakes = glakes_hylak[hylak_key].value_counts()

    # --- Step 2: Identify unique 1:1 matches
    unique_hylak_ids = hylak_counts_gwp[hylak_counts_gwp == 1].index.intersection(
        hylak_counts_glakes[hylak_counts_glakes == 1].index
    )
    if verbose:
        print(f"✅ Step 1: Found {len(unique_hylak_ids):,} clean 1:1 Hylak matches")

    # --- Step 3: Identify glakes_ids with multiple Hylak_ids (1:many)
    glakes_to_hylak = glakes_hylak.groupby(glakes_key)[hylak_key].nunique()
    multi_hylak_glakes = glakes_to_hylak[glakes_to_hylak > 1].index
    if verbose:
        print(f"✅ Step 2: Found {len(multi_hylak_glakes):,} glakes_ids linked to multiple Hylak_ids (1:many)")

    # --- Step 4: Keep valid glakes rows (either 1:1 or 1:many)
    valid_glakes = glakes_hylak[
        (glakes_hylak[hylak_key].isin(unique_hylak_ids)) |
        (glakes_hylak[glakes_key].isin(multi_hylak_glakes))
    ]
    if verbose:
        print(f"✅ Step 3: Kept {len(valid_glakes):,} glakes rows after filtering invalid Hylak_ids")

    # --- Step 5: Remove Hylak_ids that map to multiple glakes_ids (ambiguous)
    hylak_to_glakes = glakes_hylak.groupby(hylak_key)[glakes_key].nunique()
    ambiguous_hylak = hylak_to_glakes[hylak_to_glakes > 1].index
    before = len(valid_glakes)
    valid_glakes = valid_glakes[~valid_glakes[hylak_key].isin(ambiguous_hylak)]
    if verbose:
        removed = before - len(valid_glakes)
        print(f"✅ Step 4: Removed {removed:,} ambiguous Hylak_ids mapping to multiple glakes_ids")

    # --- Step 6: Merge cleaned subsets
    merged = pd.merge(
        gwp_lakes,
        valid_glakes,
        on=hylak_key,
        how=how
    )

    merged.rename(columns={"geometry_x": "gwp_geometry", "geometry_y": "glakes_geometry"}, inplace=True)
    merged.drop(columns=["glakes_geometry"], inplace=True)

    if verbose:
        print(f"🏁 Final merge completed using method '{how}'")
        print(f"   → Merged DataFrame has {len(merged):,} rows")

    unique_hylak_ids_after = merged[hylak_key].unique()

    return merged, unique_hylak_ids_after
