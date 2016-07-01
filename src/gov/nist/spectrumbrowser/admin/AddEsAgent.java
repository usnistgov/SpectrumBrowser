/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.admin;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;

/**
 * Add EsAgents - for 
 * @author mranga
 *
 */

public class AddEsAgent {

	private VerticalPanel verticalPanel;
	private Admin admin;
	private TextBox agentNameTextBox;
	private TextBox agentKeyTextBox;
	private ESAgents spectrumPolicing;

	public AddEsAgent(Admin admin, ESAgents spectrumPolicing,
			VerticalPanel verticalPanel) {
		this.verticalPanel = verticalPanel;
		this.admin = admin;
		this.spectrumPolicing = spectrumPolicing;
 
	}
	
	public void draw() {
		verticalPanel.clear();
		HTML html = new HTML("<H2>Add a sensing agent</H2>");
		verticalPanel.add(html);
		Grid grid = new Grid(3,2);
		grid.setText(0, 0, "Agent ID");
		agentNameTextBox = new TextBox();
		grid.setWidget(0, 1, agentNameTextBox);
		agentKeyTextBox = new TextBox();
		grid.setText(1, 0, "Agent Key (password)");
		grid.setWidget(1,1,agentKeyTextBox);
		verticalPanel.add(grid);
		HorizontalPanel buttonPanel = new HorizontalPanel();
		Button applyButton = new Button("Apply");
		applyButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				if (agentNameTextBox.getText() == null || agentNameTextBox.getText().length() == 0) {
					Window.alert("Please enter agent ID");
					return;
				}
				if ( agentKeyTextBox.getText() == null || agentKeyTextBox.getText().length() == 0) {
					Window.alert("Please enter valid agent key");
					return;
				}
			
				JSONObject jsonObject  = new JSONObject();
				jsonObject.put("agentName", new JSONString(agentNameTextBox.getText()));
				jsonObject.put("key", new JSONString(agentKeyTextBox.getText()));
				Admin.getAdminService().addEsAgent(jsonObject.toString(), spectrumPolicing);
			}});
		buttonPanel.add(applyButton);
		Button cancelButton = new Button("Cancel");
		cancelButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				spectrumPolicing.draw();				
			}});
		buttonPanel.add(cancelButton);
		
		Button logoffButton = new Button("Log Off");
		logoffButton.addClickHandler( new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		buttonPanel.add(logoffButton);
		
		verticalPanel.add(buttonPanel);
		
	}
	

}
