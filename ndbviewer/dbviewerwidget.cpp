#include "dbviewerwidget.h"
#include "ui_dbviewerwidget.h"

DBViewerWidget::DBViewerWidget(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::DBViewerWidget)
{
    ui->setupUi(this);
}

DBViewerWidget::~DBViewerWidget()
{
    delete ui;
}
