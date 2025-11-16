flowchart TD
    A[Start Game] --> B[Load dataset & initialize scores]
    B --> C[Randomly select a review]
    C --> D[Display review to player]
    D --> E[Player selects sentiment via radio button]
    E --> F[AI model predicts sentiment]
    F --> G[Reveal true sentiment from dataset]
    G --> H[Compare guesses with true sentiment]
    H --> I[Update scores & agreement counter]
    I --> J[Increase round number]
    J --> K{More rounds left?}
    K -->|Yes| C
    K -->|No| L[Show final scoreboard & winner]
    L --> M[Offer restart option]
    M -->|Restart| B
    M -->|Exit| N[End]
