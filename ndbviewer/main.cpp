#include "dbviewerwidget.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    DBViewerWidget w;
    w.show();

    return a.exec();
}
