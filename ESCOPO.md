# Protótipo local de análise de filas — EPS7002

## Objetivo
Demonstrar uma ferramenta de apoio à decisão para um pequeno estabelecimento: usar dados reais para compreender filas e comparar mudanças no atendimento. A apresentação pode assumir o formato de demonstração de produto, sustentada pelo estudo de caso acadêmico.

## Estrutura proposta
- Front-end: HTML, CSS e JavaScript, com interface em português, responsiva e acessível.
- Back-end: Python, inicialmente com biblioteca padrão, responsável por validar entradas, calcular indicadores e executar simulações.
- Execução local: servidor vinculado a 127.0.0.1; interface e API na mesma origem.
- Arquivos CSV para importar/exportar dados; sem login, publicação ou banco de dados nesta versão.
- Dados de demonstração explicitamente identificados. Dados reais mantidos separados dos testes.

## Fluxo da interface
1. Dados: registrar manualmente ou importar CSV com identificador anônimo, chegada, início, fim e recurso; definir período de observação e recursos disponíveis. Incluir exportação para preservar a coleta.
2. Cenários: manter o cenário atual como referência, criar alternativas nomeadas e ajustar demanda, duração de atendimento e número de atendentes.
3. Resultados: comparar espera média, tempo médio no sistema, tamanho médio da fila, utilização e quantidade de atendimentos concluídos. Identificar origem de cada resultado: observado, teórico ou simulado.

## Controles essenciais
- Adicionar atendimento e importar/exportar coleta.
- Criar cenário, renomear e excluir cenário alternativo.
- Aumentar demanda em 20% como atalho para um campo editável.
- Alterar duração média de atendimento em percentual e quantidade de atendentes.
- Executar comparação e exportar resultados.

## Significado dos cenários
- Demanda +20% significa multiplicar a taxa de chegada por 1,20 no modelo. Não significa aumentar a espera em 20% nem duplicar linhas do CSV.
- Atendimento mais rápido significa reduzir a duração do serviço; a taxa de atendimento deve ser recalculada de forma coerente.
- Alterar atendentes muda a capacidade e pode exigir outro modelo analítico.
- Fórmulas estacionárias só serão exibidas quando suas hipóteses e condições de estabilidade forem atendidas. Sobrecarga terá explicação específica; simulação em horizonte finito poderá mostrar crescimento da fila.

## Modelagem e validação
- Escolher o modelo de filas após verificar o sistema, os dados e os materiais do Moodle.
- Calcular indicadores observados e parâmetros com unidades explícitas e tratamento de registros incompletos nas bordas da observação.
- Calcular tamanho médio da fila por tempo de permanência em cada estado, evitando média apenas nas chegadas.
- Implementar simulação de eventos discretos do fluxo escolhido, com atividades e recursos reais, sementes reproduzíveis e múltiplas repetições.
- Validar fórmulas com exemplos de resposta conhecida e simulação com casos pequenos verificáveis; comparar o cenário atual com observações e informar variabilidade.
- Preservar dados originais ao criar cenários; não transformar hipóteses em registros observados.
- Confirmar com o professor a contagem do triplo de atividades/recursos na parte de simulação.

## Etapas pequenas de construção
1. Definir escopo e estrutura (este documento).
2. Definir o sistema real, fluxo e contrato de coleta; preparar a base local de front-end e back-end.
3. Implementar entrada de dados e indicadores observados, com validação e exportação.
4. Implementar o modelo de filas adequado e controles de cenários, verificando cálculos.
5. Implementar e validar a simulação ampliada; comparar resultados e sua variabilidade.
6. Refinar apresentação visual e preparar demonstração, relatório e declaração de uso de IA.

## Decisões pendentes
- Estabelecimento definido: mercado próximo à casa da dupla. Fluxo real dos caixas e outras etapas ainda serão observados.
- Modelos e ferramentas usados nos slides da disciplina.
- Interpretação da exigência de ampliação para simulação.

## Limite da primeira versão
Uma ferramenta para o estudo escolhido, sem infraestrutura comercial. Os resultados apoiam comparação de cenários dentro das hipóteses documentadas; sua validade depende da coleta e da validação do modelo.

## Primeira versão implementada em 03/11/2026
Interface e back-end locais, CSV fictício para mercado no pico, entrada manual/importação/exportação, indicadores observados, cenários M/M/c e simulação FIFO de caixas. A simulação ampliada da parte B e a adequação das hipóteses ao mercado real permanecem para etapa posterior. Veja README.md e GUIA_COLETA.md.

## Evolução para gestor genérico
A marca da aplicação passa a Fluxo — Gestor de filas. O estabelecimento é metadado da coleta, não parte fixa da interface. Angelone identifica somente o exemplo fictício. Reprodução SVG controlada da coleta ou da primeira execução dos cenários, com pausa, reinício, velocidade e navegação temporal. Mantida a hipótese de fila única FIFO com postos equivalentes; a interface genérica não altera o alcance matemático do modelo.

## Importação e recursos por tipo
Página inicial limpa, envio de CSV, configuração da janela real, quantidades convencionais/autoatendimento e classificação dos IDs. Painel oculto até análise válida. Prévia e reprodução separam convencionais com operador em cima e totens embaixo. Simulação usa serviços por tipo e exige hipótese de duração relativa quando falta amostra de um tipo utilizado. M/M/c não aplicável a cenários mistos. Nenhuma classificação automática por nome de ID ou transformação de dados convencionais em observações de totens.

## Massa de teste com maior carga
Configuração corrigida pelo usuário para 4 convencionais + 6 totens, sem caixas rápidos. Novo Angeloni_pico.csv com 968 registros sintéticos e preenchimento de tipos e janela a partir das colunas declaradas no CSV, sempre revisável. Origem preservada como SINTETICO; interface usa Dados de teste e Teste gerado. Sem validação estatística com observações reais.


## Atualização: coleta por tipo e decisão de capacidade
Use dados/Angeloni_pico_por_tipo.csv para teste e dados/modelo_coleta_por_tipo.csv como cabeçalho. Na coluna caixa informe somente C (convencional) ou CA (autoatendimento). Não precisa identificar o equipamento físico. Chegada, início e fim continuam necessários para medir a espera observada e a duração do serviço. Registre a fila e os horários reais, sem inventar tempos desconhecidos.

capacidade_convencional e capacidade_autoatendimento são colunas opcionais repetidas por sessão: informam a capacidade da coleta e sugerem as quantidades iniciais da configuração. A escolha de capacidade para projetar é revisável na tela. Dados antigos com IDs físicos continuam aceitos e podem ser classificados na configuração.

A projeção inicial mantém as chegadas, durações e tipos registrados e redistribui clientes entre todos os postos disponíveis daquele tipo, em ordem de chegada. A espera observada não muda quando a capacidade muda. A fila é FIFO dentro do tipo escolhido; não supomos migração entre tipos. Alterar demanda usa as repetições Poisson; a coluna Espera redistribuída conserva as chegadas e varia apenas capacidade/duração. Ocupação observada não é mostrada porque a capacidade projetada não comprova a capacidade histórica.

A reprodução inicial agora mostra a projeção redistribuída, sem postos artificiais sem dados. Não é uma reprodução literal dos antigos IDs. As alternativas Poisson mostram a primeira execução de 30, com tipos sorteados nas proporções da coleta. Modelagem de escolha de modalidade, filas independentes e ajuda compartilhada ainda depende do estudo real.
