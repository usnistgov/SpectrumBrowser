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
	private TextBox commentTextBox;
	private ESAgents spectrumPolicing;

	public AddEsAgent(Admin admin, ESAgents spectrumPolicing,
			VerticalPanel verticalPanel) {
		this.verticalPanel = verticalPanel;
		this.admin = admin;
		this.spectrumPolicing = spectrumPolicing;
 
	}
	
	public void draw() {
		verticalPanel.clear();
		HTML html = new HTML("<H2>Add a Spectrum Cop.</H2>");
		verticalPanel.add(html);
		Grid grid = new Grid(3,2);
		grid.setText(0, 0, "Server ID");
		agentNameTextBox = new TextBox();
		grid.setWidget(0, 1, agentNameTextBox);
		agentKeyTextBox = new TextBox();
		grid.setText(1, 0, "Server Key");
		grid.setWidget(1,1,agentKeyTextBox);
		grid.setText(2,0, "Comment");
		commentTextBox = new TextBox();
		grid.setWidget(2, 1, commentTextBox);
		verticalPanel.add(grid);
		HorizontalPanel buttonPanel = new HorizontalPanel();
		Button applyButton = new Button("Apply");
		applyButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				if (agentNameTextBox.getText() == null || agentNameTextBox.getText().length() == 0) {
					Window.alert("Please enter server ID");
					return;
				}
				if ( agentKeyTextBox.getText() == null || agentKeyTextBox.getText().length() == 0) {
					Window.alert("Please enter valid server key");
					return;
				}
				if ( commentTextBox.getText() != null && commentTextBox.getText().length() > 256) {
					Window.alert("Comment too long - please shorten it to < 256 chars.");
				}
				JSONObject jsonObject  = new JSONObject();
				jsonObject.put("agentName", new JSONString(agentNameTextBox.getText()));
				jsonObject.put("key", new JSONString(agentKeyTextBox.getText()));
				if ( commentTextBox.getText() != null) {
					jsonObject.put("comment", new JSONString(commentTextBox.getText()));
				}
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
