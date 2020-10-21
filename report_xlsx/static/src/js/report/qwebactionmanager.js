// © 2017 Creu Blanca
// License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).
odoo.define('report_xml.report', function(require){
'use strict';

var ActionManager= require('web.ActionManager');
var crash_manager = require('web.crash_manager');
var framework = require('web.framework');

ActionManager.include({
    _executeReportAction: function (action, options){
        var self = this;
        console.log('fffff',action)
        var cloned_action = _.clone(action);
        if (cloned_action.report_type === 'xlsx') {
            framework.blockUI();
            var report_xlsx_url = 'report/xlsx/' + cloned_action.report_name;
            if(cloned_action.context.active_ids){
                report_xlsx_url += '/' + cloned_action.context.active_ids.join(',');
            }else{
                report_xlsx_url += '?options=' + encodeURIComponent(JSON.stringify(cloned_action.data));
                report_xlsx_url += '&context=' + encodeURIComponent(JSON.stringify(cloned_action.context));
            }
            self.getSession().get_file({
                url: report_xlsx_url,
                data: {data: JSON.stringify([
                    report_xlsx_url,
                    cloned_action.report_type
                                            ]),
                          context:JSON.stringify(cloned_action.context),

                       },
                context:cloned_action.context,
                error: crash_manager.rpc_error.bind(crash_manager),
                success: function (){
                    if(cloned_action && options && !cloned_action.dialog){
                        options.on_close();
                    }
                }
            });
            framework.unblockUI();
            return $.Deferred().reject();;
        }
        return self._super(action, options);
    },
//    /**
//     * Overrides to handle the 'ir.actions.report' actions.
//     *
//     * @override
//     * @private
//     */
//    _handleAction: function (action, options) {
//        console.log('ggggg',action)
//        if (action.type === 'ir.actions.report') {
//            return this._executeReportAction(action, options);
//        }
//        return this._super.apply(this, arguments);
//    },
});
});
