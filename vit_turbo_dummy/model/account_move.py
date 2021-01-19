from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class account_move(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    @api.model_cr
    def init(self):
        _logger.info("creating vit_turbo_validate_account_move function...")
        self.env.cr.execute("""CREATE OR REPLACE FUNCTION public.vit_create_dummy_account_move(
                v_company_id integer,
                v_debit_account_id integer,
                v_credit_account_id integer,
                v_journal_id integer,
                v_count integer)
                RETURNS void
                LANGUAGE 'plpgsql'

                COST 100
                VOLATILE 
                
            AS $BODY$
            DECLARE
                v_partner record;
                v_partner_name TEXT;
                v_partner_ref TEXT;
                v_partner_email TEXT;
                v_partner_phone TEXT;
                v_partner_street TEXT;
                v_partner_id INTEGER;
                v_next_sequence RECORD;
                v_sequence RECORD;
                v_sequence_id INTEGER;
                v_prefix TEXT;
                v_am_name TEXT;
                v_am_id INTEGER;
                v_journal RECORD;
                v_amount NUMERIC;
                v_account RECORD;
                v_user_type_id INTEGER;
                v_aml_id INTEGER;
            BEGIN

                FOR i IN 1..v_count
                LOOP
                
                    --- CREATE PARTNER

                    v_partner_name = 'PARNTER ' || LPAD( i::TEXT, 5, '0');
                    v_partner_ref = 'P'||LPAD( i::TEXT, 5, '0');
                    v_partner_email = LPAD( i::TEXT, 5, '0') || '@example.com';
                    v_partner_phone = LPAD( i::TEXT, 10, '0');	
                    v_partner_street = 'PARTNER STREET ' || LPAD( i::TEXT, 10, '0');
                    
                    SELECT * FROM res_partner WHERE ref = v_partner_ref INTO v_partner;
                    IF v_partner IS NULL THEN

                        INSERT INTO res_partner (display_name, name, email, phone, mobile, street, active, 
                            invoice_warn, picking_warn, purchase_warn, sale_warn, customer, is_company, ref) 
                        VALUES (v_partner_name, v_partner_name, v_partner_email, v_partner_phone, v_partner_phone, v_partner_street, true, 
                            'no-message','no-message','no-message','no-message', true, true, v_partner_ref) 
                        RETURNING ID INTO v_partner_id;
                    ELSE
                        v_partner_id = v_partner.id;
                    END IF;
                    
                    RAISE NOTICE '%', v_partner_id;
                    
                    
                    --- CREATE ACCOUNT MOVE

                    --- browse journal -------------------
                    SELECT * from account_journal where id = v_journal_id INTO v_journal;
                    v_sequence_id = v_journal.sequence_id;

                    SELECT * FROM "ir_sequence" WHERE "ir_sequence".id = v_sequence_id INTO v_sequence;
                    SELECT * FROM "ir_sequence_date_range" WHERE ((("ir_sequence_date_range"."sequence_id" = v_sequence_id)  
                        AND  ("ir_sequence_date_range"."date_from" <= CURRENT_DATE))  AND  ("ir_sequence_date_range"."date_to" >= CURRENT_DATE)) 
                        ORDER BY "ir_sequence_date_range"."id"  FOR UPDATE NOWAIT limit 1 
                        INTO v_next_sequence;
                        
                    UPDATE ir_sequence_date_range SET number_next=number_next+1 WHERE id=v_next_sequence.id ;
                    v_prefix = replace(v_sequence.prefix, '%(range_year)s', extract(year from now())::text);
                    v_prefix = replace(v_prefix, '%(year)s', extract(year from now())::text);
                    v_prefix = replace(v_prefix, '%(month)s', extract(month from now())::text);

                    v_am_name = coalesce(v_prefix,'') || LPAD(v_next_sequence.number_next::text, v_sequence.padding, '0')|| coalesce(v_sequence.suffix,'');
                    INSERT INTO "account_move" ("id", "create_uid", "create_date", "write_uid", "write_date", "auto_reverse", "date", "journal_id", "name", "narration", "ref", "state", "partner_id", "company_id","amount") 
                        VALUES (nextval('account_move_id_seq'), 2, (now() at time zone 'UTC'), 2, (now() at time zone 'UTC'), false, CURRENT_DATE, v_journal_id, v_am_name, NULL, 'DUMMY'||v_partner_name, 'posted', v_partner_id, v_company_id, v_amount) RETURNING id 
                        INTO v_am_id;

                    v_amount = random()*1000000;

                    
                    --- CREATE ACCOUNT MOVE LINE DEBIT
                    SELECT * from account_account where id = v_debit_account_id INTO v_account;
                    v_user_type_id = v_account.user_type_id;
                    
                    INSERT INTO "account_move_line" ("id", "create_uid", "create_date", "write_uid", "write_date", "account_id", "amount_currency", "analytic_account_id", "blocked", "company_currency_id", "credit", "currency_id", "date_maturity", "debit", "invoice_id", "move_id", "name", "partner_id", "product_id", "product_uom_id", "quantity", "reconciled", "tax_exigible", "tax_line_id","journal_id", "date", "balance", "ref", "user_type_id", "company_id") 
                        VALUES (nextval('account_move_line_id_seq'), 2, (now() at time zone 'UTC'), 2, (now() at time zone 'UTC'), v_account.id, 0.0, NULL, false, 12, 0.0, NULL, CURRENT_DATE, v_amount, null, v_am_id, v_account.name, v_partner_id, null, null, 1, false, true, NULL, v_journal.id, CURRENT_DATE, -v_amount, v_am_name, v_user_type_id, v_company_id) RETURNING id INTO v_aml_id;
                    

                    --- CREATE ACCOUNT MOVE LINE CREDIT		
                    SELECT * from account_account where id = v_credit_account_id INTO v_account;
                    v_user_type_id = v_account.user_type_id;		
                    
                    INSERT INTO "account_move_line" ("id", "create_uid", "create_date", "write_uid", "write_date", "account_id", "amount_currency", "analytic_account_id", "blocked", "company_currency_id", "credit", "currency_id", "date_maturity", "debit", "invoice_id", "move_id", "name", "partner_id", "product_id", "product_uom_id", "quantity", "reconciled", "tax_exigible", "tax_line_id", "company_id", "journal_id", "date", "balance", "tax_base_amount", "ref", "amount_residual", "user_type_id") 
                        VALUES (nextval('account_move_line_id_seq'), 2, (now() at time zone 'UTC'), 2, (now() at time zone 'UTC'), v_account.id, 0.0, NULL, false, 12, v_amount, NULL, CURRENT_DATE, '0.00', null, v_am_id, v_account.name, v_partner_id, NULL, NULL, '1.000', false, true, NULL, v_company_id, v_journal.id, CURRENT_DATE, -v_amount, 0, v_am_name, -v_amount, v_user_type_id);

                    
                END LOOP;

            END;
            $BODY$;
        """)