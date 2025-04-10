function createXlsxReport(reportsData) {
    try {
        if (reportsData.length === 0) {
            alert("Нет данных для создания отчета!");
            return;
        }

        const wb = XLSX.utils.book_new();
        const wsData = [
            ['№', '+', '-', 'Верно', 'Неверно', '%', 'Оценка']
        ];

        reportsData.forEach((report, index) => {
            wsData.push([
                `Работа ${report.work_number}`,
                report.correct_answers_count,
                report.incorrect_answers_count,
                report.correct_questions.join(', '),
                report.incorrect_question_numbers.join(', '),
                `${report.score_percentage}%`,
                report.grade
            ]);
        });

        const totalStudents = reportsData.length;
        const excellentCount = reportsData.filter(report => report.grade === 5).length;
        const goodCount = reportsData.filter(report => report.grade === 4).length;
        const satisfactoryCount = reportsData.filter(report => report.grade === 3).length;

        const successRate = ((excellentCount + goodCount + satisfactoryCount) / totalStudents * 100).toFixed(2) + '%';
        const knowledgeQuality = ((excellentCount + goodCount) / totalStudents * 100).toFixed(2) + '%';

        wsData.push(['', '', '', '', '', 'Успеваемость:', successRate]);
        wsData.push(['', '', '', '', '', 'Качество знаний:', knowledgeQuality]);

        const ws = XLSX.utils.aoa_to_sheet(wsData);
        XLSX.utils.book_append_sheet(wb, ws, 'Отчеты');
        XLSX.writeFile(wb, 'отчет.xlsx', { bookType: 'xlsx', type: 'binary' });
    } catch (error) {
        console.error("Ошибка при создании XLSX:", error);
        alert("Произошла ошибка при создании отчета. Проверьте консоль разработчика.");
    }
}