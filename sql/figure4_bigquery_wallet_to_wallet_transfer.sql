WITH sc AS (
    /* Get a list of smart contract addresses */
    SELECT
        DISTINCT address
    FROM
        `bigquery-public-data.crypto_ethereum.contracts`
),
exchange_and_vasps AS (
    SELECT
        DISTINCT address
    FROM
        /* Internal labels */
        `circle-ds-pipelines.multichain.address_labels`
    WHERE
        vertical = 'Exchanges and VASPs'
        AND STARTS_WITH(address, '0x')
        AND length(address) = 42
),
erc20_exchange_deposit_address AS (
    SELECT
        /* Mark sender as Exchange deposit address (EDA) */
        DISTINCT from_address address
    FROM
        `bigquery-public-data.crypto_ethereum.token_transfers` a
        /* Join by to_address */
        LEFT JOIN `circle-ds-pipelines.multichain.address_labels` b ON a.to_address = b.address
        /* remove smart contracts */
        LEFT JOIN sc d1 ON a.from_address = d1.address
        LEFT JOIN sc d2 ON a.to_address = d2.address
    WHERE
        date(a.block_timestamp) <= '2023-03-31'
        /* Receiver is an exchange */
        AND b.subvertical = 'Exchanges'
        /* Only consider USDC USDT & WETH */
        AND lower(a.token_address) IN (
            /* USDC */
            '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
            /* USDT */
            '0xdac17f958d2ee523a2206206994597c13d831ec7',
            /* WETH */
            '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
        )
        /* Neither sender / receiver is smart contract */
        AND d1.address IS NULL
        AND d2.address IS NULL
)
SELECT
    /* Check whether or not it is direct stablecoin contract interaction */
    IF(
        b.to_address = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
        1,
        0
    ) AS w2w_transfer,
    sum(
        safe_cast(a.value AS FLOAT64) / 1.0e6
    ) AS transfer_value,
    count(DISTINCT transaction_hash) AS txn_cnt
FROM
    `bigquery-public-data.crypto_ethereum.token_transfers` a
    LEFT JOIN `bigquery-public-data.crypto_ethereum.transactions` b ON a.transaction_hash = b.hash
    LEFT JOIN exchange_and_vasps e1 ON a.from_address = e1.address
    LEFT JOIN exchange_and_vasps e2 ON a.to_address = e2.address
    LEFT JOIN erc20_exchange_deposit_address d1 ON a.from_address = d1.address
    LEFT JOIN erc20_exchange_deposit_address d2 ON a.to_address = d2.address
WHERE
    /* Inception to 2023/03/31 */
    date(a.block_timestamp) <= '2023-03-31'
    AND a.token_address = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
    /*Neither sender and receiver not exchanges or deposit addresses*/
    AND e1.address IS NULL
    AND e2.address IS NULL
    AND d1.address IS NULL
    AND d2.address IS NULL
GROUP BY
    1
ORDER BY
    1