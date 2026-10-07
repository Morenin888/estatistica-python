import argparse
import csv
import io
import math
import sys
from pathlib import Path

def number(text, context="Valor", decimal_comma=False):
    text = str(text).strip()
    if not text:
        raise ValueError(f"{context}: campo vazio; informe um número.")
    try:
        value = float(text.replace(",", ".") if decimal_comma else text)
    except (ValueError, OverflowError) as error:
        raise ValueError(f"{context}: {text!r} não é um número válido.") from error
    if not math.isfinite(value):
        raise ValueError(f"{context}: {text!r} não é um número finito.")
    return value

def validate_values(values):
    values = [number(v, f"Observação {i}") for i, v in enumerate(values, 1)]
    if not values:
        raise ValueError("Informe pelo menos um número.")
    return values

def parse_numbers(text):
    separator = ";" if ";" in text else ","
    return [number(v, f"Valor {i}", separator == ";") for i, v in enumerate(text.split(separator), 1)]

def load_csv(path, coluna=None, cabecalho=False):
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except FileNotFoundError as error:
        raise ValueError(f"Arquivo não encontrado: {path}.") from error
    except PermissionError as error:
        raise ValueError(f"Sem permissão para ler: {path}.") from error
    except UnicodeError as error:
        raise ValueError("O arquivo deve estar codificado em UTF-8.") from error
    if not text.strip():
        raise ValueError("O arquivo está vazio.")
    sample = text[:65536]
    try:
        detector = csv.Sniffer()
        detector.preferred = [";", "\t", ","]
        delimiter = detector.sniff(sample, delimiters=";\t,").delimiter
    except csv.Error:
        first = next((line for line in sample.splitlines() if line.strip()), "")
        delimiter = ";" if ";" in first else "\t" if "\t" in first else ","
    index, name = None, None
    if coluna is not None:
        if isinstance(coluna, int) or str(coluna).strip().lstrip("+-").isdigit():
            index = int(coluna) - 1
            if index < 0:
                raise ValueError("O índice da coluna deve ser um inteiro a partir de 1.")
        else:
            name = str(coluna).strip()
            if not name or not cabecalho:
                raise ValueError("Informe um nome de coluna e use --cabecalho.")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=delimiter, strict=True)
    physical, values, first, previous = text.splitlines(keepends=True), [], True, 0
    try:
        for row in reader:
            start, end = previous + 1, reader.line_num
            previous = end
            if not "".join(physical[start - 1:end]).strip():
                continue
            header = first and cabecalho
            if header and name is not None:
                matches = [i for i, value in enumerate(row) if value.strip() == name]
                if len(matches) != 1:
                    reason = "não encontrada" if not matches else "aparece mais de uma vez"
                    raise ValueError(f"Linha {start}: coluna {name!r} {reason} no cabeçalho.")
                index = matches[0]
            if index is not None and index >= len(row):
                raise ValueError(f"Linha {start}: coluna {index + 1} não existe.")
            if not header:
                cells = enumerate(row) if index is None else [(index, row[index])]
                values.extend(number(v, f"Linha {start}, coluna {i + 1}", delimiter != ",") for i, v in cells)
            first = False
    except csv.Error as error:
        raise ValueError(f"CSV inválido próximo à linha {reader.line_num}: {error}.") from error
    if not values:
        raise ValueError("O arquivo não contém dados numéricos para analisar.")
    return values

def ungrouped_stats(values):
    import statistics
    return {"mean": statistics.mean(values), "median": statistics.median(values), "mode": statistics.mode(values)}

def discrete_frequency(values):
    counts, rows, cumulative = {}, [], 0
    for value in validate_values(values):
        counts[value] = counts.get(value, 0) + 1
    for value, frequency in sorted(counts.items()):
        cumulative += frequency
        rows.append((value, frequency, cumulative))
    return rows

def weighted_mean(rows):
    n, scale = sum(row[1] for row in rows), max(abs(row[0]) for row in rows)
    if scale == 0:
        return 0.0
    total, correction = 0.0, 0.0
    for value, frequency, _ in rows:
        term = (value / scale) * (frequency / n)
        partial = total + term
        correction += (total - partial) + term if abs(total) >= abs(term) else (term - partial) + total
        total = partial
    return max(-1.0, min(1.0, total + correction)) * scale

def midpoint(a, b):
    return (a + b) / 2 if a <= 0 <= b else a + (b - a) / 2

def rank_from_frequency(rows, rank):
    return next(value for value, _, cumulative in rows if cumulative >= rank)

def discrete_stats(rows):
    n, maximum = rows[-1][2], max(row[1] for row in rows)
    left, right = (rank_from_frequency(rows, p) for p in ((n + 1) // 2, n // 2 + 1))
    modes = [value for value, frequency, _ in rows if frequency == maximum]
    return weighted_mean(rows), midpoint(left, right), modes

def make_classes(values):
    values = validate_values(values)
    n, low, high = len(values), min(values), max(values)
    if low == high:
        return [{"lower": low, "upper": high, "fi": n, "Fi": n}]
    k = math.ceil(1 + 3.322 * math.log10(n))
    width = number(high - low, "Amplitude total") / k
    bounds = [low + i * width for i in range(k)] + [high]
    if width <= 0 or any(a >= b for a, b in zip(bounds, bounds[1:])):
        raise ValueError("Limites de classes se repetem por falta de precisão numérica; reescalone os dados.")
    frequencies = [0] * k
    for value in values:
        index = min(int((value - low) / width), k - 1)
        while index > 0 and value < bounds[index]:
            index -= 1
        while index < k - 1 and value >= bounds[index + 1]:
            index += 1
        frequencies[index] += 1
    classes, cumulative = [], 0
    for i, frequency in enumerate(frequencies):
        cumulative += frequency
        classes.append({"lower": bounds[i], "upper": bounds[i + 1], "fi": frequency, "Fi": cumulative})
    return classes

def grouped_mean(classes):
    return weighted_mean([(midpoint(c["lower"], c["upper"]), c["fi"], c["Fi"]) for c in classes])

def quantile_grouped(classes, position):
    position = number(position, "Posição")
    if position <= 0:
        return classes[0]["lower"]
    if position >= classes[-1]["Fi"]:
        return classes[-1]["upper"]
    previous = 0
    for c in classes:
        if c["fi"] and c["Fi"] >= position:
            return c["lower"] + (position - previous) / c["fi"] * (c["upper"] - c["lower"])
        previous = c["Fi"]

def grouped_median(classes):
    return quantile_grouped(classes, classes[-1]["Fi"] / 2)

def grouped_mode(classes):
    if len(classes) == 1 and classes[0]["lower"] == classes[0]["upper"]:
        return [classes[0]["lower"]], "Dados constantes: moda exata."
    frequencies = [c["fi"] for c in classes]
    maximum = max(frequencies)
    indices = [i for i, f in enumerate(frequencies) if f == maximum]
    if maximum == 1 or len(indices) == len(classes) > 1:
        return [], "Não há classe modal predominante; a moda não é única."
    modes, observation = [], "Há empate: as estimativas não determinam uma moda única." if len(indices) > 1 else ""
    neighbors = [0] + frequencies + [0]
    for i in indices:
        d1, d2 = maximum - neighbors[i], maximum - neighbors[i + 2]
        if d1 + d2 == 0:
            observation += " No platô, d1 + d2 = 0 impede interpolação."
        else:
            c = classes[i]
            mode = c["lower"] + d1 / (d1 + d2) * (c["upper"] - c["lower"])
            if mode not in modes:
                modes.append(mode)
    return modes, observation

def summary(mean, median, modes):
    text = ", ".join(f"{value:.12g}" for value in modes) or "não definida"
    print(f"Média: {mean:.12g} | Mediana: {median:.12g} | Moda(s): {text}")

def print_results(values):
    values = validate_values(values)
    stats, rows, classes = ungrouped_stats(values), discrete_frequency(values), make_classes(values)
    if not all(math.isfinite(value) for value in stats.values()):
        raise ValueError("statistics produziu um resultado não finito; use valores de menor magnitude.")
    n = len(values)
    print(f"Dados carregados com sucesso! (n = {n} elementos)")
    print("\nPARTE 1: DADOS NÃO AGRUPADOS (statistics)")
    for name, key in (("Média", "mean"), ("Mediana", "median"), ("Moda", "mode")):
        print(f"{name}: {stats[key]:.12g}")
    mean, median, modes = discrete_stats(rows)
    if len(modes) > 1:
        print("statistics.mode retorna a primeira moda encontrada em caso de empate.")
    print("\nPARTE 2: FREQUÊNCIA DISCRETA (cálculo pela tabela)")
    print(f"{'Valor (xi)':>16} | {'fi':>8} | {'Fi':>8}")
    for value, fi, Fi in rows:
        print(f"{value!r:>16} | {fi:>8} | {Fi:>8}")
    summary(mean, median, modes)
    if len(modes) == len(rows) > 1 and rows[0][1] == 1:
        print("Todos os valores ocorrem uma vez: não há moda predominante.")
    print("\nPARTE 3: FREQUÊNCIA COM INTERVALOS (Python nativo)")
    print(f"Sturges: k = {math.ceil(1 + 3.322 * math.log10(n))} | Classes efetivas = {len(classes)}")
    print(f"Amplitude total = {max(values) - min(values):.12g} | h = {classes[0]['upper'] - classes[0]['lower']:.12g}")
    print(f"{'Intervalo de Classe':>35} | {'fi':>6} | {'Fi':>6}")
    for i, c in enumerate(classes):
        interval = f"[{c['lower']!r} - {c['upper']!r}{']' if i == len(classes) - 1 else ')'}"
        print(f"{interval:>35} | {c['fi']:>6} | {c['Fi']:>6}")
    modes, observation = grouped_mode(classes)
    print("Medidas agrupadas são estimativas; moda pelo método de Czuber:")
    summary(grouped_mean(classes), grouped_median(classes), modes)
    if observation:
        print(observation)
    for name, positions in (("Quartis", (("Q1", .25), ("Q3", .75))), ("Decis", (("D2", .2), ("D7", .7))),
                            ("Percentis", (("P15", .15), ("P22", .22), ("P63", .63), ("P70", .7)))):
        print(name + ": " + " | ".join(f"{label} = {quantile_grouped(classes, n * p):.12g}" for label, p in positions))

def menu():
    while True:
        print("\nANALISADOR ESTATÍSTICO\n[1] Inserir dados\n[2] Carregar CSV\n[0] Sair")
        option = input("Escolha a opção: ").strip()
        if option == "0":
            print("Programa encerrado.")
            return 0
        if option not in ("1", "2"):
            print("Opção inválida. Escolha 1, 2 ou 0.")
            continue
        try:
            if option == "1":
                values = parse_numbers(input("Números (ex.: 1,2,3 ou 1,5;2,5): "))
            else:
                path = input("Caminho do arquivo CSV: ").strip()
                answer = input("Possui cabeçalho? [s/N]: ").strip().lower()
                if answer not in ("", "n", "nao", "não", "s", "sim"):
                    raise ValueError("Resposta inválida; informe s ou n.")
                column = input("Coluna (nome ou índice; Enter para todas): ").strip()
                values = load_csv(path, column or None, answer in ("s", "sim"))
            print_results(values)
        except (OSError, ValueError, OverflowError) as error:
            print(f"Erro: {error}\nRetornando ao menu; verifique os dados.")

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and not argv[0].startswith("-") and Path(argv[0].replace("\\", "/")).name == "main.py":
        argv = argv[1:]
    parser = argparse.ArgumentParser(description="Analisador estatístico descritivo")
    parser._optionals.title = "Opções"
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--data", "--dados", help="números separados por vírgula ou ;")
    group.add_argument("-f", "--file", "--csv", help="arquivo CSV em UTF-8")
    parser.add_argument("--cabecalho", action="store_true", help="pula a primeira linha não vazia do CSV")
    parser.add_argument("--coluna", help="nome ou índice da coluna CSV a partir de 1")
    args = parser.parse_args(argv)
    if args.file is None and (args.coluna is not None or args.cabecalho):
        parser.error("--coluna e --cabecalho só podem ser usados com --csv/--file")
    try:
        if args.data is None and args.file is None:
            return menu()
        print_results(parse_numbers(args.data) if args.data is not None else load_csv(args.file, args.coluna, args.cabecalho))
        return 0
    except (OSError, UnicodeError, ValueError, OverflowError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nPrograma encerrado.")
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
