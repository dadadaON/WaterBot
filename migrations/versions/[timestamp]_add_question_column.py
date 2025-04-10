"""add question column

Revision ID: [auto-generated]
Revises: [auto-generated]
Create Date: [auto-generated]

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Створюємо нову таблицю
    op.create_table(
        'service_requests_new',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('service_type', sa.String(), nullable=False),
        sa.Column('question', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    
    # Копіюємо дані
    op.execute(
        'INSERT INTO service_requests_new (id, full_name, phone, address, service_type, created_at) '
        'SELECT id, full_name, phone, address, service_type, created_at FROM service_requests'
    )
    
    # Видаляємо стару таблицю
    op.drop_table('service_requests')
    
    # Перейменовуємо нову таблицю
    op.rename_table('service_requests_new', 'service_requests')

def downgrade():
    # Видаляємо колонку question (створюємо нову таблицю без неї)
    op.create_table(
        'service_requests_new',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=False),
        sa.Column('service_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    
    # Копіюємо дані назад
    op.execute(
        'INSERT INTO service_requests_new (id, full_name, phone, address, service_type, created_at) '
        'SELECT id, full_name, phone, address, service_type, created_at FROM service_requests'
    )
    
    # Видаляємо стару таблицю
    op.drop_table('service_requests')
    
    # Перейменовуємо нову таблицю
    op.rename_table('service_requests_new', 'service_requests') 