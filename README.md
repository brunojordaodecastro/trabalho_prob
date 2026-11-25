# Fluxo — Gestor de filas

Protótipo acadêmico local para uma fila de atendimento com caixas convencionais e/ou autoatendimento. HTML/CSS/JavaScript e API Python com biblioteca padrão, sem instalar pacotes.

## Iniciar
Execute `.\iniciar.ps1` na pasta do projeto ou `python server.py` com Python 3.10+. Abra http://127.0.0.1:7002. Ctrl+C encerra. O inicializador também procura o Python do runtime do Codex neste computador.

## Restaurar após formatar o computador

1. Instale Python 3.10 ou superior, disponível no terminal como `python` (no Windows, o comando `py` também pode ser usado).
2. Baixe este repositório em Code → Download ZIP e extraia a pasta, ou clone com `git clone https://github.com/brunojordaodecastro/trabalho_prob.git`.
3. Abra um terminal na pasta extraída e execute `python server.py` (ou `py server.py`). Não é necessário instalar pacotes nem ter o Codex.
4. Abra http://127.0.0.1:7002 e importe `dados/Angeloni_pico_por_tipo.csv` para testar, ou seu CSV de coleta real.

Este backup inclui código, CSVs presentes em `dados/`, documentação, histórico `.codex` e prévias em `output/`. Os dados carregados apenas na página não são salvos automaticamente: exporte-os e guarde o CSV antes da formatação. Arquivos fora desta pasta, fotos e documentos externos não estão incluídos.

Verificação do backup em 25/11/2026: 8 dos 13 testes passam. Os outros 5 dependem dos arquivos antigos `dados/Angelone_pico_FICTICIO.csv` e `dados/Angeloni_pico.csv`, ausentes na pasta original do backup. O teste de redistribuição com o CSV atual passa; as massas antigas não foram recriadas.

## Fluxo de uso
1. A página começa vazia, com a apresentação e o botão Enviar arquivo CSV. Nenhum exemplo carrega automaticamente.
2. Selecione um CSV completo. A aplicação valida registros e identifica os postos, sem calcular os resultados ainda.
3. Configure quantos caixas convencionais e quantos totens existem, disponíveis durante todo o período. De 1 a 20 postos no total.
4. Informe C/CA no CSV; a distribuição entre equipamentos é calculada pelo aplicativo. A prévia atualiza com convencionais em cima e totens embaixo.
5. Corrija o período para a janela real da coleta, incluindo intervalos sem chegadas. A sugestão usa primeira e última chegada e não comprova a duração da observação.
6. Se um tipo configurado não tem tempos no CSV, informe Duração do totem (% da convencional). 120 significa 20% mais demorado. Essa opção abre automaticamente quando necessária. Com amostras dos dois tipos, usamos seus próprios tempos.
7. Clique Analisar e abrir painel. Só então aparecem indicadores, reprodução e resultados.

Use Configurar operação para revisar as entradas. Cenários podem variar os dois tipos separadamente, além de demanda e duração do serviço. Alterações exigem novo cálculo.

## Dados
Massa de teste disponível: `dados/Angeloni_pico_por_tipo.csv`, com 968 atendimentos gerados em 03/11/2026, chegadas entre 16:00 e 19:00 e capacidade de coleta de quatro convencionais e seis totens. A coluna caixa usa C/CA para identificar a modalidade. É um teste de carga severa, sem calibração com dados reais do Angeloni. A fila observada chega a 353 pessoas; a última saída ocorre às 20:38:29. As massas antigas com IDs físicos não estão presentes neste backup.

Cabeçalho vazio em `dados/modelo_coleta_por_tipo.csv`; protocolo em `GUIA_COLETA.md`. O nome da operação vem da coluna opcional estabelecimento. Campos opcionais tipo_caixa (normal/self), inicio_observacao e fim_observacao preenchem a configuração para revisão; itens é metadado e não impõe restrição de roteamento. A origem SINTETICO identifica dados gerados sem exibir avisos repetidos de fictício. CSV original preservado ao classificar e simular. A classificação e a razão de duração são configurações da análise, informadas novamente na reimportação.

Aceita CSV com vírgula, ponto e vírgula ou tabulação. Nenhum upload é gravado no servidor. Não há salvamento automático: exporte a coleta antes de fechar. Recarregar retorna à tela vazia. Exportação de cenários inclui quantidades por tipo e hipótese de duração relativa.

## Modelos e limites
- Indicadores observados: tempos e taxas, fila média e ocupação. Médias de espera seguem chegadas em [início, fim), acompanhadas até terminar. Áreas temporais limitam-se à janela, incluindo clientes anteriores com histórico completo.
- Simulação: FIFO dentro do tipo escolhido C/CA, capacidade constante. O posto disponível daquele tipo atende a próxima chegada. Sem modelagem de migração entre tipos, prioridade, abandono ou funcionário compartilhado auxiliando totens.
- Chegadas Poisson constantes; durações por reamostragem do tipo de posto, usando registros completos relevantes à janela. Sem amostra, aplica a hipótese de duração relativa. Variação de serviço multiplica ambas as distribuições.
- 30 repetições com início vazio. Chegadas na janela, acompanhamento até saída. Fila e ocupação são médias temporais; concluídos são saídas na janela. Desvio padrão entre médias das execuções não é intervalo de confiança.
- M/M/c somente para cenários com um tipo de posto, sujeito a serviços exponenciais e postos equivalentes. Cenários mistos exibem Não aplicável; sobrecarga homogênea não tem média estacionária finita.
- Reprodução SVG: coleta ou execução 1 do cenário, nunca média agregada. Movimentos ilustrativos sem tempo adicional no modelo. Início/pausa, reinício, velocidade e linha do tempo. Sem autoplay; pausa ao ocultar aba, respeita movimento reduzido. Desenha até 30 pessoas esperando e conta excedentes.

As hipóteses ainda dependem de validação com dados reais. A simulação ampliada da parte B permanece dependente do fluxo real e da orientação do professor.

## Testes e estrutura
`python -m unittest -v` verifica fórmulas conhecidas, sobrecarga, entradas, janelas, sementes, recursos heterogêneos e exigência de hipótese quando não há amostra de um tipo.

server.py: HTTP/API. filas.py: validação e cálculos. static/: interface. dados/: exemplos. test_filas.py: testes. .codex: histórico. Vinculado a 127.0.0.1, destinado a uma sessão local por vez.

## Geração da massa de carga
Semente 731026. Chegadas Poisson por blocos de meia hora com taxas planejadas 160, 260, 420, 460, 380 e 180 por hora. Serviços com duração dependente do tipo e do número de itens, variação lognormal e interrupções ocasionais de pagamento/conferência. Fila única, sem abandono, início vazio e capacidade constante; todos acompanhados até o término. Parâmetros e contagens estão em dados/Angeloni_pico_metadados.json. As médias da simulação podem diferir da reprodução: o motor atual aproxima a taxa de chegada como constante ao longo de toda a janela. A aprovação do teste funcional não valida essa hipótese para o estudo real.


## Atualização: coleta por tipo e decisão de capacidade
Use dados/Angeloni_pico_por_tipo.csv para teste e dados/modelo_coleta_por_tipo.csv como cabeçalho. Na coluna caixa informe somente C (convencional) ou CA (autoatendimento). Não precisa identificar o equipamento físico. Chegada, início e fim continuam necessários para medir a espera observada e a duração do serviço. Registre a fila e os horários reais, sem inventar tempos desconhecidos.

capacidade_convencional e capacidade_autoatendimento são colunas opcionais repetidas por sessão: informam a capacidade da coleta e sugerem as quantidades iniciais da configuração. A escolha de capacidade para projetar é revisável na tela. Dados antigos com IDs físicos continuam aceitos e podem ser classificados na configuração.

A projeção inicial mantém as chegadas, durações e tipos registrados e redistribui clientes entre todos os postos disponíveis daquele tipo, em ordem de chegada. A espera observada não muda quando a capacidade muda. A fila é FIFO dentro do tipo escolhido; não supomos migração entre tipos. Alterar demanda usa as repetições Poisson; a coluna Espera redistribuída conserva as chegadas e varia apenas capacidade/duração. Ocupação observada não é mostrada porque a capacidade projetada não comprova a capacidade histórica.

A reprodução inicial agora mostra a projeção redistribuída, sem postos artificiais sem dados. Não é uma reprodução literal dos antigos IDs. As alternativas Poisson mostram a primeira execução de 30, com tipos sorteados nas proporções da coleta. Modelagem de escolha de modalidade, filas independentes e ajuda compartilhada ainda depende do estudo real.
