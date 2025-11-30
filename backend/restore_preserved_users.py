"""
Script de restauration des utilisateurs préservés
À exécuter après le déploiement pour restaurer les identifiants des utilisateurs existants
"""
import asyncio
import sys
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PRESERVED_USERS = [
    {
        "first_name": "MOUHAMAD BACHIR",
        "last_name": "DIAGNE",
        "email": "mouhamadbachirdiagne@gmail.com",
        "level": "beginner",
        "temp_password": "Kalama12d751"
    },
    {
        "first_name": "Khadija",
        "last_name": "Dione",
        "email": "diatoudione444@gmail.com",
        "level": "beginner",
        "temp_password": "Kalamaaba898"
    },
    {
        "first_name": "Salimata",
        "last_name": "Ndiaye",
        "email": "ndiayesalimata434@gmail.com",
        "level": "intermediate",
        "temp_password": "Kalamafa23cc"
    },
    {
        "first_name": "Mouhamath",
        "last_name": "Lo",
        "email": "mouhamathlo94@gmail.com",
        "level": "beginner",
        "temp_password": "Kalama492fb5"
    },
    {
        "first_name": "Saliou",
        "last_name": "Faye",
        "email": "salioufaye238@gmail.com",
        "level": "intermediate",
        "temp_password": "Kalamae8f64d"
    },
    {
        "first_name": "Khady",
        "last_name": "Ngom",
        "email": "ngomkhadijh@gmail.com",
        "level": "beginner",
        "temp_password": "Kalama5e82f2"
    },
    {
        "first_name": "Awa",
        "last_name": "Ndiaye",
        "email": "awa36782@gmail.com",
        "level": "intermediate",
        "temp_password": "Kalama4b048a"
    }
]

async def restore_users():
    """Restaure ou crée les utilisateurs préservés"""
    mongo_url = os.environ.get('MONGO_URL')
    if not mongo_url:
        print("❌ ERREUR: Variable MONGO_URL non définie")
        return
    
    client = AsyncIOMotorClient(mongo_url)
    db = client.kalamaenglish_db
    
    # Obtenir l'ID du professeur par défaut
    teacher = await db.users.find_one({"role": "teacher"}, {"_id": 0})
    teacher_id = teacher['id'] if teacher else None
    
    print("=" * 60)
    print("🔄 RESTAURATION DES UTILISATEURS PRÉSERVÉS")
    print("=" * 60)
    print()
    
    created_count = 0
    updated_count = 0
    
    for user_data in PRESERVED_USERS:
        email = user_data["email"]
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        
        if existing_user:
            # Mettre à jour l'utilisateur existant
            password_hash = pwd_context.hash(user_data["temp_password"])
            
            update_data = {
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "level": user_data["level"],
                "temporary_password": user_data["temp_password"],
                "password_hash": password_hash,
                "is_active": True
            }
            
            await db.users.update_one(
                {"email": email},
                {"$set": update_data}
            )
            
            print(f"✅ MAJ: {user_data['first_name']} {user_data['last_name']}")
            print(f"   📧 {email}")
            print(f"   🔑 {user_data['temp_password']}")
            print(f"   📚 {user_data['level']}")
            print()
            updated_count += 1
        else:
            # Créer le nouvel utilisateur
            new_user = {
                "id": str(uuid4()),
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": email,
                "phone": "",
                "level": user_data["level"],
                "temporary_password": user_data["temp_password"],
                "password_hash": pwd_context.hash(user_data["temp_password"]),
                "is_active": True,
                "role": "student",
                "course_type": "individual",
                "assigned_teacher": teacher_id
            }
            
            await db.users.insert_one(new_user)
            
            print(f"➕ CRÉÉ: {user_data['first_name']} {user_data['last_name']}")
            print(f"   📧 {email}")
            print(f"   🔑 {user_data['temp_password']}")
            print(f"   📚 {user_data['level']}")
            print()
            created_count += 1
    
    print("=" * 60)
    print(f"✅ RESTAURATION TERMINÉE")
    print(f"   Créés: {created_count}")
    print(f"   Mis à jour: {updated_count}")
    print(f"   Total: {created_count + updated_count}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(restore_users())
