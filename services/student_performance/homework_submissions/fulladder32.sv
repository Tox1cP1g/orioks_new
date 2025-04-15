module fulladder32 (
    input  logic [31:0] a_i,    // 32-битный входной вектор a_i
    input  logic [31:0] b_i,    // 32-битный входной вектор b_i
    input  logic carry_i,       // Входной бит переноса
    output logic [31:0] sum_o,  // 32-битный выходной вектор суммы
    output logic carry_o        // Выходной бит переноса
);

    // Вспомогательные провода для передачи промежуточных битов переноса
    logic [7:0] carry;

    // Первый 4-битный сумматор (биты 0-3)
    fulladder4 fa0 (
        .a_i(a_i[3:0]),
        .b_i(b_i[3:0]),
        .carry_i(carry_i),
        .sum_o(sum_o[3:0]),
        .carry_o(carry[0])
    );

    // Второй 4-битный сумматор (биты 4-7)
    fulladder4 fa1 (
        .a_i(a_i[7:4]),
        .b_i(b_i[7:4]),
        .carry_i(carry[0]),
        .sum_o(sum_o[7:4]),
        .carry_o(carry[1])
    );

    // Третий 4-битный сумматор (биты 8-11)
    fulladder4 fa2 (
        .a_i(a_i[11:8]),
        .b_i(b_i[11:8]),
        .carry_i(carry[1]),
        .sum_o(sum_o[11:8]),
        .carry_o(carry[2])
    );

    // Четвертый 4-битный сумматор (биты 12-15)
    fulladder4 fa3 (
        .a_i(a_i[15:12]),
        .b_i(b_i[15:12]),
        .carry_i(carry[2]),
        .sum_o(sum_o[15:12]),
        .carry_o(carry[3])
    );

    // Пятый 4-битный сумматор (биты 16-19)
    fulladder4 fa4 (
        .a_i(a_i[19:16]),
        .b_i(b_i[19:16]),
        .carry_i(carry[3]),
        .sum_o(sum_o[19:16]),
        .carry_o(carry[4])
    );

    // Шестой 4-битный сумматор (биты 20-23)
    fulladder4 fa5 (
        .a_i(a_i[23:20]),
        .b_i(b_i[23:20]),
        .carry_i(carry[4]),
        .sum_o(sum_o[23:20]),
        .carry_o(carry[5])
    );

    // Седьмой 4-битный сумматор (биты 24-27)
    fulladder4 fa6 (
        .a_i(a_i[27:24]),
        .b_i(b_i[27:24]),
        .carry_i(carry[5]),
        .sum_o(sum_o[27:24]),
        .carry_o(carry[6])
    );

    // Восьмой 4-битный сумматор (биты 28-31)
    fulladder4 fa7 (
        .a_i(a_i[31:28]),
        .b_i(b_i[31:28]),
        .carry_i(carry[6]),
        .sum_o(sum_o[31:28]),
        .carry_o(carry[7])
    );

    // Выходной бит переноса
    assign carry_o = carry[7];

endmodule