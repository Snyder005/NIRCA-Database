#ifndef DBVIEWERWIDGET_H
#define DBVIEWERWIDGET_H

#include <QWidget>

namespace Ui {
class DBViewerWidget;
}

class DBViewerWidget : public QWidget
{
    Q_OBJECT

public:
    explicit DBViewerWidget(QWidget *parent = 0);
    ~DBViewerWidget();

private:
    Ui::DBViewerWidget *ui;
};

#endif // DBVIEWERWIDGET_H
