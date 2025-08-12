with adv_col1:
    st.subheader("Investment Efficacy")
    plot_data = df_filtered[(df_filtered['Investment'] > 0) & (df_filtered['Money Saved'] > 0)]
    
    if not plot_data.empty:
        if show_percentage:
            # Calculate totals for percentage view
            total_investment_all = plot_data['Investment'].sum()
            total_savings_all = plot_data['Money Saved'].sum()

            plot_data['Investment %'] = (plot_data['Investment'] / total_investment_all) * 100
            plot_data['Savings %'] = (plot_data['Money Saved'] / total_savings_all) * 100
            
            x_axis, y_axis = 'Investment %', 'Savings %'
            x_label, y_label = '% of Total Investment', '% of Total Savings'
            title_text = "Relative Contribution to Investment vs. Savings"
        else:
            x_axis, y_axis = 'Investment', 'Money Saved'
            x_label, y_label = 'Investment (€)', 'Annual Money Saved (€)'
            title_text = "Investment vs. Annual Savings"

        fig_bubble = px.scatter(
            plot_data,
            x=x_axis,
            y=y_axis,
            size='Energy Saved',
            color='Category',
            hover_name='Measure',
            size_max=60,
            title=title_text,
            template="plotly_white"
        )
        
        fig_bubble.update_layout(
            xaxis_title=x_label,
            yaxis_title=y_label,
            legend_title=analysis_type
        )
        st.plotly_chart(fig_bubble, use_container_width=True)
    else:
        st.info("No data with both investment and savings to display in the bubble chart.")
