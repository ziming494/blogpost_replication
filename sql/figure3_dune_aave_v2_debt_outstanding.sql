with current_market_ as (
    SELECT
        r.*,
        t.symbol,
        rank() over(
            partition by t.symbol,
            date(evt_block_time)
            order by
                r.evt_block_number desc,
                r.evt_index desc
        ) as rank
    FROM
        aave_v2_ethereum.LendingPool_evt_ReserveDataUpdated r
        LEFT JOIN tokens.erc20 t ON t.contract_address = r.reserve
        AND t.blockchain = 'ethereum'
),
current_market as (
    SELECT
        *,
        date(evt_block_time) as ds
    FROM
        current_market_
    WHERE
        rank = 1
        and symbol in ('USDC', 'USDT')
),
reserves as (
    SELECT
        r.*,
        'ethereum' as blockchain,
        t.symbol,
        t.decimals
    FROM
        aave_v2_ethereum.LendingPoolConfigurator_evt_ReserveInitialized r
        INNER JOIN tokens.erc20 t ON t.contract_address = r.asset
        AND t.blockchain = 'ethereum'
        and t.symbol in ('USDC', 'USDT')
),
variableDebtChanges as (
    SELECT
        contract_address,
        evt_tx_hash,
        evt_index,
        evt_block_number,
        evt_block_time,
        index,
        cast(value as int256) as raw_change,
        'mint' as type
    FROM
        aave_v2_ethereum.VariableDebtToken_evt_Mint m
    UNION
    ALL
    SELECT
        contract_address,
        evt_tx_hash,
        evt_index,
        evt_block_number,
        evt_block_time,
        index,
        - cast(amount as int256) as raw_change,
        'burn' as type
    FROM
        aave_v2_ethereum.VariableDebtToken_evt_Burn b
),
scaled_amts as (
    SELECT
        r.symbol,
        date(variableDebtChanges.evt_block_time) as ds,
        sum(variableDebtChanges.raw_change) as raw_debt_changes,
        sum(
            variableDebtChanges.raw_change / pow(10, r.decimals) / variableDebtChanges.index * pow(10, 27)
        ) as scaled_variable_debt
    FROM
        variableDebtChanges
        LEFT JOIN reserves r ON r.variableDebtToken = variableDebtChanges.contract_address
    WHERE
        r.decimals is not null
    GROUP BY
        1,
        2
    order by
        1,
        2
),
cumu_scaled_amts as (
    select
        *,
        sum(scaled_variable_debt) over(
            partition by symbol
            order by
                ds
        ) as total_scaled_variable_debt
    from
        scaled_amts
)
SELECT
    cumu_scaled_amts.symbol,
    cumu_scaled_amts.ds,
    current_market.variableBorrowIndex,
    total_scaled_variable_debt * current_market.variableBorrowIndex / pow(10, 27) as current_variable_debt
FROM
    cumu_scaled_amts
    LEFT JOIN current_market ON cumu_scaled_amts.symbol = current_market.symbol
    and cumu_scaled_amts.ds = current_market.ds
    and cumu_scaled_amts.symbol = current_market.symbol
order by
    1,
    2